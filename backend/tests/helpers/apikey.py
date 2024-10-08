import uuid
from datetime import datetime

import callee

from auditize.apikey.models import Apikey
from auditize.apikey.service import create_apikey
from auditize.permissions.models import Permissions

from .http import HttpTestHelper
from .permissions.constants import DEFAULT_PERMISSIONS


class PreparedApikey:
    def __init__(self, id: str, key: str, data: dict):
        self.id = id
        self.key = key
        self.data = data

    @staticmethod
    def prepare_data(extra=None):
        return {"name": f"Apikey {uuid.uuid4()}", **(extra or {})}

    @classmethod
    async def create(cls, client: HttpTestHelper, data=None) -> "PreparedApikey":
        if data is None:
            data = cls.prepare_data()
        resp = await client.assert_post(
            "/apikeys",
            json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], resp.json()["key"], data)

    @staticmethod
    def prepare_model(*, permissions=None) -> Apikey:
        model = Apikey(name=f"Apikey {uuid.uuid4()}")
        if permissions is not None:
            model.permissions = Permissions.model_validate(permissions)
        return model

    @classmethod
    async def inject_into_db(cls, apikey: Apikey = None) -> "PreparedApikey":
        if apikey is None:
            apikey = cls.prepare_model()
        apikey_id, key = await create_apikey(apikey)
        return cls(
            id=str(apikey_id),
            key=key,
            data={
                "name": apikey.name,
            },
        )

    @classmethod
    async def inject_into_db_with_permissions(
        cls, permissions: dict
    ) -> "PreparedApikey":
        return await cls.inject_into_db(cls.prepare_model(permissions=permissions))

    def expected_document(self, extra=None):
        return {
            "_id": uuid.UUID(self.id),
            "name": self.data["name"],
            "key_hash": callee.IsA(str),
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
        c = HttpTestHelper.spawn()
        c.headers["Authorization"] = f"Bearer {self.key}"
        return c
