from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator
from uuid import UUID, uuid4

import callee
from httpx import Response

from auditize.database import get_dbm
from auditize.i18n.lang import Lang
from auditize.permissions.models import Permissions
from auditize.resource.service import create_resource_document
from auditize.user.models import User
from auditize.user.service import (
    build_document_from_user,
    get_user,
    hash_user_password,
)

from .http import HttpTestHelper, get_cookie_by_name
from .log_filter import PreparedLogFilter
from .permissions.constants import DEFAULT_PERMISSIONS


class PreparedUser:
    def __init__(self, id: str, data: dict, password=None):
        self.id = id
        self.data = data
        self.password = password

    @staticmethod
    def prepare_data(extra=None):
        rand = str(uuid4())
        return {
            "first_name": f"John {rand}",
            "last_name": f"Doe {rand}",
            "email": f"john.doe_{rand}@example.net",
            **(extra or {}),
        }

    @classmethod
    async def create(cls, client: HttpTestHelper, data=None) -> "PreparedUser":
        if data is None:
            data = cls.prepare_data()
        resp = await client.assert_post(
            "/users",
            json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], data)

    @staticmethod
    def prepare_model(*, password="dummypassword", permissions=None, lang=None) -> User:
        rand = str(uuid4())
        model = User(
            first_name=f"John {rand}",
            last_name=f"Doe {rand}",
            email=f"john.doe_{rand}@example.net",
            password_hash=hash_user_password(password),
            lang=lang or Lang.EN,
        )
        if permissions is not None:
            model.permissions = Permissions.model_validate(permissions)
        return model

    @classmethod
    async def inject_into_db(
        cls, user: User = None, password="dummypassword"
    ) -> "PreparedUser":
        if user is None:
            user = cls.prepare_model(password=password)
        # FIXME: auditize.users.service.save_user should be used here
        user_id = await create_resource_document(
            get_dbm().core_db.users, build_document_from_user(user)
        )
        return cls(
            id=str(user_id),
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            },
            password=password,
        )

    async def expire_password_reset_token(self):
        await get_dbm().core_db.users.update_one(
            {"_id": UUID(self.id)},
            {
                "$set": {
                    "password_reset_token.expires_at": datetime.now(timezone.utc)
                    - timedelta(days=1)
                }
            },
        )

    @property
    def email(self) -> str:
        return self.data["email"]

    @property
    async def password_reset_token(self) -> str | None:
        user_model = await get_user(UUID(self.id))
        return (
            user_model.password_reset_token.token
            if user_model.password_reset_token
            else None
        )

    async def log_in(self, client: HttpTestHelper) -> Response:
        return await client.assert_post(
            "/auth/user/login",
            json={"email": self.email, "password": self.password},
            expected_status_code=200,
        )

    @asynccontextmanager
    async def client(self) -> AsyncIterator[HttpTestHelper]:
        async with HttpTestHelper.spawn() as client:
            await self.log_in(client)
            yield client

    async def get_session_token(self, client: HttpTestHelper) -> str:
        resp = await self.log_in(client)
        return get_cookie_by_name(resp, "session").value

    def expected_document(self, extra=None) -> dict:
        password_reset_token = {
            "token": callee.Regex(r"^[0-9a-f]{64}$"),
            "expires_at": callee.IsA(datetime),
        }
        return {
            "_id": UUID(self.id),
            "first_name": self.data["first_name"],
            "last_name": self.data["last_name"],
            "email": self.data["email"],
            "lang": self.data.get("lang", "en"),
            "permissions": DEFAULT_PERMISSIONS,
            "password_hash": callee.IsA(str) if self.password else None,
            "created_at": callee.IsA(datetime),
            "password_reset_token": None if self.password else password_reset_token,
            "authenticated_at": None,
            **(extra or {}),
        }

    def expected_api_response(self, extra=None) -> dict:
        return {
            "id": self.id,
            "first_name": self.data["first_name"],
            "last_name": self.data["last_name"],
            "email": self.data["email"],
            "lang": self.data.get("lang", "en"),
            "permissions": DEFAULT_PERMISSIONS,
            "authenticated_at": None,
            **(extra or {}),
        }

    async def create_log_filter(self, data):
        async with self.client() as client:
            resp = await client.assert_post_created("/users/me/logs/filters", json=data)
        return PreparedLogFilter(resp.json()["id"], data)
