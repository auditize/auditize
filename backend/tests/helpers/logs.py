from datetime import datetime

import callee
from bson import ObjectId
from icecream import ic

from .utils import DATETIME_FORMAT

# A valid ObjectId, but not existing in the database
UNKNOWN_OBJECT_ID = "65fab045f097fe0b9b664c99"


class PreparedLog:
    def __init__(self, id: str, data: dict, repo):
        from .repos import PreparedRepo  # avoid circular import

        self.id = id
        self.data = data
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
            "node_path": [{"ref": "1", "name": "Customer 1"}],
            **extra,
        }

    def expected_api_response(self, extra=None) -> dict:
        expected: dict[str, any] = {
            "source": {},
            "actor": None,
            "resource": None,
            "details": {},
            "tags": [],
            "attachments": [],
            "id": self.id,
            **self.data,
            "saved_at": DATETIME_FORMAT,
        }
        for tag in expected["tags"]:
            tag.setdefault("category", None)
            tag.setdefault("name", None)
        if expected["actor"]:
            expected["actor"].setdefault("extra", [])
        if expected["resource"]:
            expected["resource"].setdefault("extra", [])
        return {**expected, **(extra or {})}

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
