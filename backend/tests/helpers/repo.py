from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import callee
from elasticsearch import AsyncElasticsearch

from auditize.database import get_dbm
from auditize.database.dbm import open_db_session
from auditize.repo.service import create_repo
from auditize.repo.sql_models import Repo

from .http import HttpTestHelper
from .log import PreparedLog


class PreparedRepo:
    def __init__(self, id: str, data: dict, log_db_name: str):
        self.id = id
        self.data = data
        self.log_db_name = log_db_name

    @property
    def es(self) -> AsyncElasticsearch:
        return get_dbm().elastic_client

    @staticmethod
    def prepare_data(extra=None):
        return {"name": f"Repo {uuid4()}", **(extra or {})}

    @classmethod
    async def create(cls, data, log_db_name: str):
        if not data:
            data: dict[str, Any] = cls.prepare_data()
        model_data = data.copy()
        if "log_i18n_profile_id" in model_data:
            model_data["log_i18n_profile_id"] = UUID(model_data["log_i18n_profile_id"])
        async with open_db_session() as session:
            repo = await create_repo(
                session, Repo(**model_data), log_db_name=log_db_name
            )
        return cls(str(repo.id), data, log_db_name)

    @staticmethod
    def build_expected_api_response(extra=None):
        return {
            "id": callee.IsA(str),
            "created_at": callee.IsA(str),
            "status": "enabled",
            "log_i18n_profile_id": None,
            "retention_period": None,
            "stats": None,
            **(extra or {}),
        }

    def expected_api_response(self, extra=None) -> dict:
        return self.build_expected_api_response(
            {
                "id": self.id,
                "name": self.data["name"],
                "status": self.data.get("status", "enabled"),
                "retention_period": self.data.get("retention_period", None),
                "log_i18n_profile_id": self.data.get("log_i18n_profile_id", None),
                **(extra or {}),
            }
        )

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
            await self.es.update(
                index=self.log_db_name,
                id=log_id,
                doc={"saved_at": saved_at},
                refresh=True,
            )
        return PreparedLog(log_id, data, self)

    async def create_log_with(
        self, client: HttpTestHelper, extra: dict, *, saved_at: datetime = None
    ):
        return await self.create_log(
            client, PreparedLog.prepare_data(extra), saved_at=saved_at
        )

    async def create_log_with_entity_path(
        self,
        client: HttpTestHelper,
        entity_path: list[str],
        *,
        saved_at: datetime = None,
    ):
        return await self.create_log_with(
            client,
            {
                "entity_path": [
                    {"name": entity, "ref": entity} for entity in entity_path
                ]
            },
            saved_at=saved_at,
        )

    async def update_status(self, client: HttpTestHelper, status: str):
        await client.assert_patch_ok(f"/repos/{self.id}", json={"status": status})

    async def get_log(self, log_id: str | UUID) -> dict | None:
        resp = await self.es.get(index=self.log_db_name, id=log_id)
        return resp["_source"]

    async def get_log_count(self) -> int:
        resp = await self.es.count(
            index=self.log_db_name,
            query={"match_all": {}},
        )
        return resp["count"]
