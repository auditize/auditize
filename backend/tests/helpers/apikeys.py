import uuid
from datetime import datetime

import callee
from bson import ObjectId

from auditize.apikeys.models import Apikey
from auditize.apikeys.service import create_apikey
from auditize.common.db import DatabaseManager
from auditize.permissions.models import Permissions

from .http import HttpTestHelper, create_http_client
from .permissions.constants import DEFAULT_PERMISSIONS


class PreparedApikey:
    def __init__(self, id: str, token: str, data: dict, dbm: DatabaseManager):
        self.id = id
        self.token = token
        self.data = data
        self.dbm = dbm

    @staticmethod
    def prepare_data(extra=None):
        return {"name": f"Apikey {uuid.uuid4()}", **(extra or {})}

    @classmethod
    async def create(
        cls, client: HttpTestHelper, dbm: DatabaseManager, data=None
    ) -> "PreparedApikey":
        if data is None:
            data = cls.prepare_data()
        resp = await client.assert_post(
            "/apikeys",
            json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], resp.json()["token"], data, dbm)

    @staticmethod
    def prepare_model(*, permissions=None) -> Apikey:
        model = Apikey(name=f"Apikey {uuid.uuid4()}")
        if permissions is not None:
            model.permissions = Permissions.model_validate(permissions)
        return model

    @classmethod
    async def inject_into_db(
        cls, dbm: DatabaseManager, apikey: Apikey = None
    ) -> "PreparedApikey":
        if apikey is None:
            apikey = cls.prepare_model()
        apikey_id, token = await create_apikey(dbm, apikey)
        return cls(
            id=str(apikey_id),
            token=token,
            data={
                "name": apikey.name,
            },
            dbm=dbm,
        )

    @classmethod
    async def inject_into_db_with_permissions(
        cls, dbm: DatabaseManager, permissions: dict
    ) -> "PreparedApikey":
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
