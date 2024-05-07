import uuid
from datetime import datetime

import callee
from bson import ObjectId

from auditize.common.db import DatabaseManager
from auditize.integrations.models import Integration
from auditize.integrations.service import create_integration
from auditize.permissions.models import Permissions

from .http import HttpTestHelper, create_http_client
from .permissions.constants import DEFAULT_PERMISSIONS


class PreparedIntegration:
    def __init__(self, id: str, token: str, data: dict, dbm: DatabaseManager):
        self.id = id
        self.token = token
        self.data = data
        self.dbm = dbm

    @staticmethod
    def prepare_data(extra=None):
        return {"name": f"Integration {uuid.uuid4()}", **(extra or {})}

    @classmethod
    async def create(
        cls, client: HttpTestHelper, dbm: DatabaseManager, data=None
    ) -> "PreparedIntegration":
        if data is None:
            data = cls.prepare_data()
        resp = await client.assert_post(
            "/integrations",
            json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], resp.json()["token"], data, dbm)

    @staticmethod
    def prepare_model(*, permissions=None) -> Integration:
        model = Integration(name=f"Integration {uuid.uuid4()}")
        if permissions is not None:
            model.permissions = Permissions.model_validate(permissions)
        return model

    @classmethod
    async def inject_into_db(
        cls, dbm: DatabaseManager, integration: Integration = None
    ) -> "PreparedIntegration":
        if integration is None:
            integration = cls.prepare_model()
        integration_id, token = await create_integration(dbm, integration)
        return cls(
            id=str(integration_id),
            token=token,
            data={
                "name": integration.name,
            },
            dbm=dbm,
        )

    @classmethod
    async def inject_into_db_with_permissions(
        cls, dbm: DatabaseManager, permissions: dict
    ) -> "PreparedIntegration":
        return await cls.inject_into_db(dbm, cls.prepare_model(permissions=permissions))

    def expected_document(self, extra=None):
        return {
            "_id": ObjectId(self.id),
            "name": self.data["name"],
            "token_hash": callee.IsA(str),
            "created_at": callee.IsA(datetime),
            "permissions": DEFAULT_PERMISSIONS,
            **(extra or {}),
        }

    def expected_api_response(self, extra=None):
        return {
            "id": self.id,
            "name": self.data["name"],
            "permissions": DEFAULT_PERMISSIONS,
            **(extra or {}),
        }

    def client(self) -> HttpTestHelper:
        c = create_http_client()
        c.headers["Authorization"] = f"Bearer {self.token}"
        return c
