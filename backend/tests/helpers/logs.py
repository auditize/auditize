from datetime import datetime

import callee
from bson import ObjectId
from icecream import ic

from .http import HttpTestHelper
from .repos import PreparedRepo

# A valid ObjectId, but not existing in the database
UNKNOWN_OBJECT_ID = "65fab045f097fe0b9b664c99"


class PreparedLog:
    def __init__(self, id: str, data: dict, repo: PreparedRepo):
        self.id = id
        self.data = data
        self.repo = repo

    @staticmethod
    def prepare_data(extra=None) -> dict:
        """
        By default, the log data is minimal viable.
        """

        extra = extra or {}

        return {
            "event": {
                "name": "user_login",
                "category": "authentication",
            },
            "node_path": [{"id": "1", "name": "Customer 1"}],
            **extra,
        }

    def expected_api_response(self, extra=None) -> dict:
        expected = {
            "source": {},
            "actor": None,
            "resource": None,
            "details": {},
            "tags": [],
            "attachments": [],
            "id": self.id,
            **self.data,
            "saved_at": callee.Regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"),
        }
        for tag in expected["tags"]:
            tag.setdefault("category", None)
            tag.setdefault("name", None)
        if expected["actor"]:
            expected["actor"].setdefault("extra", {})
        if expected["resource"]:
            expected["resource"].setdefault("extra", {})
        return {**expected, **(extra or {})}

    @classmethod
    async def create(
        cls,
        client: HttpTestHelper,
        repo: PreparedRepo,
        data: dict = None,
        *,
        saved_at: datetime = None,
    ):
        if data is None:
            data = cls.prepare_data()
        resp = await client.assert_post(
            f"/repos/{repo.id}/logs", json=data, expected_status_code=201
        )
        log_id = resp.json()["id"]
        if saved_at:
            repo.db.logs.update_one(
                {"_id": ObjectId(log_id)}, {"$set": {"saved_at": saved_at}}
            )
        return cls(log_id, data, repo)

    async def assert_db(self, extra=None):
        expected = self.expected_api_response(extra)

        # from expected API response, make data suitable for db comparison
        expected["saved_at"] = callee.IsA(datetime)
        del expected["id"]

        db_log = await self.repo.db.logs.find_one(
            {"_id": ObjectId(self.id)}, {"_id": 0}
        )
        ic(db_log)
        assert db_log == expected
