from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import callee

from auditize.log.db import LogDatabase
from auditize.repo.models import Repo
from auditize.repo.service import create_repo

from .http import HttpTestHelper
from .log import PreparedLog


class PreparedRepo:
    def __init__(self, id: str, data: dict, db: LogDatabase):
        self.id = id
        self.data = data
        self.db = db

    @staticmethod
    def prepare_data(extra=None):
        return {"name": f"Repo {uuid4()}", **(extra or {})}

    @classmethod
    async def create(cls, data, log_db: LogDatabase):
        if not data:
            data: dict[str, Any] = cls.prepare_data()
        model_data = data.copy()
        if "log_i18n_profile_id" in model_data:
            model_data["log_i18n_profile_id"] = UUID(model_data["log_i18n_profile_id"])
        repo_id = await create_repo(Repo(**model_data), log_db=log_db)
        return cls(str(repo_id), data, log_db)

    @staticmethod
    def build_expected_document(repo_id, data, extra=None):
        return {
            "_id": UUID(repo_id),
            "name": data["name"],
            "log_db_name": callee.IsA(str),
            "status": data.get("status", "enabled"),
            "retention_period": data.get("retention_period", None),
            "log_i18n_profile_id": (
                UUID(data["log_i18n_profile_id"])
                if "log_i18n_profile_id" in data
                else None
            ),
            "created_at": callee.IsA(datetime),
            **(extra or {}),
        }

    def expected_document(self, extra=None):
        return self.build_expected_document(self.id, self.data, extra)

    def expected_api_response(self, extra=None) -> dict:
        return {
            "id": self.id,
            "name": self.data["name"],
            "status": self.data.get("status", "enabled"),
            "retention_period": self.data.get("retention_period", None),
            "log_i18n_profile_id": self.data.get("log_i18n_profile_id", None),
            "created_at": callee.IsA(str),
            "stats": None,
            **(extra or {}),
        }

    async def create_log(
        self, client: HttpTestHelper, data: dict = None, *, saved_at: datetime = None
    ) -> PreparedLog:
        if data is None:
            data = PreparedLog.prepare_data()
        resp = await client.assert_post(
            f"/repos/{self.id}/logs", json=data, expected_status_code=201
        )
        log_id = resp.json()["id"]
        if saved_at:
            await self.db.logs.update_one(
                {"_id": UUID(log_id)}, {"$set": {"saved_at": saved_at}}
            )
        return PreparedLog(log_id, data, self)

    def create_log_with(
        self, client: HttpTestHelper, extra: dict, *, saved_at: datetime = None
    ):
        return self.create_log(
            client, PreparedLog.prepare_data(extra), saved_at=saved_at
        )

    async def create_log_with_entity_path(
        self, client: HttpTestHelper, entity_path: list[str], *, saved_at: datetime = None
    ):
        return await self.create_log_with(
            client,
            {"entity_path": [{"name": entity, "ref": entity} for entity in entity_path]},
            saved_at=saved_at,
        )

    async def update_status(self, client: HttpTestHelper, status: str):
        await client.assert_patch(
            f"/repos/{self.id}", json={"status": status}, expected_status_code=204
        )
