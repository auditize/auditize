import uuid
from datetime import datetime
from bson import ObjectId

from auditize.repos.service import create_repo
from auditize.repos.models import Repo
from auditize.common.mongo import DatabaseManager, RepoDatabase

import callee


class RepoTestHelper:
    def __init__(self, id: str, data: dict, db: RepoDatabase):
        self.id = id
        self.data = data
        self.db = db

    @staticmethod
    def prepare_data(extra=None):
        return {
            "name": f"Repo {uuid.uuid4()}",
            **(extra or {})
        }

    @classmethod
    async def create(cls, dbm: DatabaseManager):
        data = cls.prepare_data()
        repo_id = await create_repo(dbm, Repo(**data))
        repo_db = dbm.get_repo_db(repo_id)
        return cls(repo_id, data, repo_db)

    def expected_document(self, extra=None):
        return {
            "_id": ObjectId(self.id),
            "name": self.data["name"],
            "created_at": callee.IsA(datetime),
            **(extra or {})
        }

    def expected_api_response(self, extra=None):
        return {
            "id": self.id,
            "name": self.data["name"],
            "created_at": callee.IsA(str),
            "stats": None,
            **(extra or {})
        }
