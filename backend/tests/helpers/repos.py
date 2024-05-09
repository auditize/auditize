import uuid
from datetime import datetime

import callee
from bson import ObjectId

from auditize.database import DatabaseManager
from auditize.logs.db import LogDatabase, get_log_db
from auditize.repos.models import Repo
from auditize.repos.service import create_repo

from .http import HttpTestHelper


class PreparedRepo:
    def __init__(self, id: str, data: dict, db: LogDatabase):
        self.id = id
        self.data = data
        self.db = db

    @staticmethod
    def prepare_data(extra=None):
        return {"name": f"Repo {uuid.uuid4()}", **(extra or {})}

    @classmethod
    async def create(cls, dbm: DatabaseManager, data=None):
        if not data:
            data = cls.prepare_data()
        repo_id = await create_repo(dbm, Repo(**data))
        logs_db = await get_log_db(dbm, repo_id)
        return cls(str(repo_id), data, logs_db)

    def expected_document(self, extra=None):
        return {
            "_id": ObjectId(self.id),
            "name": self.data["name"],
            "created_at": callee.IsA(datetime),
            **(extra or {}),
        }

    def expected_api_response(self, extra=None) -> dict:
        return {
            "id": self.id,
            "name": self.data["name"],
            "created_at": callee.IsA(str),
            "stats": None,
            **(extra or {}),
        }

    async def create_log(
        self, client: HttpTestHelper, data: dict = None, saved_at: datetime = None
    ) -> "PreparedLog":
        from .logs import PreparedLog  # avoid circular import

        return await PreparedLog.create(client, self, data, saved_at=saved_at)
