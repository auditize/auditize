import base64
import typing
from copy import deepcopy
from typing import Any

import callee
from icecream import ic

from auditize.database import get_dbm

from .http import HttpTestHelper
from .utils import DATETIME_FORMAT

if typing.TYPE_CHECKING:
    from .repo import PreparedRepo

# A valid UUID, but not existing in the database
# FIXME: should be moved to a more general module
UNKNOWN_UUID = "e42350b9-db1c-42f9-a08a-b1265f1b9bf5"


class PreparedLog:
    def __init__(self, id: str, data: dict, repo):
        from .repo import PreparedRepo  # avoid circular import

        self.id = id
        self.data = data
        self._attachments = []
        self.repo: PreparedRepo = repo

    @staticmethod
    def prepare_data(extra=None) -> dict:
        """
        By default, the log data is minimal viable.
        """

        extra = extra or {}

        return {
            "action": {
                "type": "user_login",
                "category": "authentication",
            },
            "entity_path": [{"ref": "entity", "name": "Entity"}],
            **extra,
        }

    @staticmethod
    def prepare_data_with_entity_path(
        extra=None, *, entity_path: list[str] = None
    ) -> dict:
        return PreparedLog.prepare_data(
            {
                **extra,
                **(
                    {
                        "entity_path": [
                            {"ref": entity, "name": entity} for entity in entity_path
                        ]
                    }
                    if entity_path
                    else {}
                ),
            }
        )

    async def upload_attachment(
        self,
        client: HttpTestHelper,
        *,
        data: bytes = "some text content",
        name="attachment.txt",
        type="text_file",
        mime_type=None,
    ):
        await client.assert_post(
            f"/repos/{self.repo.id}/logs/{self.id}/attachments",
            files={"file": (name, data)},
            data={
                "type": type,
                "mime_type": mime_type,
            },
            expected_status_code=204,
        )
        self._attachments.append(
            {
                "name": name,
                "type": type,
                "mime_type": mime_type,
            }
        )

    @staticmethod
    def build_expected_api_response(data=None) -> dict:
        expected: dict[str, Any] = {
            "source": [],
            "actor": None,
            "resource": None,
            "details": [],
            "tags": [],
            "attachments": [],
            "id": callee.IsA(str),
            "saved_at": DATETIME_FORMAT,
            **(deepcopy(data) or {}),
        }
        for tag in expected["tags"]:
            tag.setdefault("ref", None)
            tag.setdefault("name", None)
        if expected["actor"]:
            expected["actor"].setdefault("extra", [])
        if expected["resource"]:
            expected["resource"].setdefault("extra", [])
        for attachment in expected["attachments"]:
            attachment["saved_at"] = DATETIME_FORMAT
        custom_fields = (
            expected["source"]
            + expected["details"]
            + (expected["actor"]["extra"] if expected["actor"] else [])
            + (expected["resource"]["extra"] if expected["resource"] else [])
        )
        for custom_field in custom_fields:
            if "type" not in custom_field:
                match custom_field["value"]:
                    case bool():
                        custom_field["type"] = "boolean"
                    case int():
                        custom_field["type"] = "integer"
                    case float():
                        custom_field["type"] = "float"
                    case _:
                        custom_field["type"] = "string"
        return expected

    def expected_api_response(self, extra=None) -> dict:
        return self.build_expected_api_response(
            {
                "id": self.id,
                "attachments": self._attachments,
                **self.data,
                **(extra or {}),
            }
        )

    def expected_db_document(self, extra=None) -> dict:
        expected = self.expected_api_response(extra)
        expected["saved_at"] = callee.IsA(str)
        for expected_attachment in expected["attachments"]:
            expected_attachment["data"] = base64.b64encode(
                expected_attachment["data"]
            ).decode()
            expected_attachment["saved_at"] = callee.IsA(str)
        expected["log_id"] = self.id
        del expected["id"]
        return expected

    async def assert_db(self, extra=None):
        expected = self.expected_db_document(extra)

        dbm = get_dbm()
        resp = await dbm.elastic_client.get(
            index=f"{self.repo.log_db_name}_read", id=self.id
        )
        db_log = resp["_source"]
        ic(db_log)
        assert db_log == expected


async def assert_elastic_log_document(
    repo: "PreparedRepo", log_id: str, expected: dict
):
    dbm = get_dbm()
    resp = await dbm.elastic_client.get(index=f"{repo.log_db_name}_read", id=log_id)
    db_log = resp["_source"]
    ic(db_log)
    assert db_log == expected
