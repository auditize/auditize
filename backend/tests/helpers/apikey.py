import uuid

import callee

from auditize.apikey.models import ApikeyCreate
from auditize.apikey.service import create_apikey
from auditize.apikey.sql_models import Apikey
from auditize.database.dbm import open_db_session
from auditize.permissions.models import PermissionsInput

from .http import HttpTestHelper
from .permissions.constants import DEFAULT_PERMISSIONS
from .utils import DATETIME_FORMAT


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
    def prepare_model(*, permissions=None) -> ApikeyCreate:
        model = ApikeyCreate(name=f"Apikey {uuid.uuid4()}")
        if permissions is not None:
            model.permissions = PermissionsInput.model_validate(permissions)
        return model

    @classmethod
    async def inject_into_db(cls, apikey: Apikey = None) -> "PreparedApikey":
        if apikey is None:
            apikey = cls.prepare_model()

        async with open_db_session() as session:
            apikey, key = await create_apikey(session, apikey)
        return cls(
            id=str(apikey.id),
            key=key,
            data={"name": apikey.name},
        )

    @classmethod
    async def inject_into_db_with_permissions(
        cls, permissions: dict
    ) -> "PreparedApikey":
        return await cls.inject_into_db(cls.prepare_model(permissions=permissions))

    @staticmethod
    def build_expected_api_response(extra=None):
        return {
            "id": callee.IsA(str),
            "permissions": DEFAULT_PERMISSIONS,
            "created_at": DATETIME_FORMAT,
            "updated_at": DATETIME_FORMAT,
            **(extra or {}),
        }

    def expected_api_response(self, extra=None):
        return self.build_expected_api_response(
            {
                "id": self.id,
                "name": self.data["name"],
                **(extra or {}),
            }
        )

    def client(self) -> HttpTestHelper:
        c = HttpTestHelper.spawn()
        c.headers["Authorization"] = f"Bearer {self.key}"
        return c
