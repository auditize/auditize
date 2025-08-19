from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import AsyncIterator
from uuid import UUID, uuid4

import callee
from httpx import Response

from auditize.database import get_core_db
from auditize.database.dbm import open_db_session
from auditize.i18n.lang import Lang
from auditize.permissions.models import PermissionsInput
from auditize.resource.service import create_resource_document
from auditize.user.models import User, UserCreate, UserUpdate
from auditize.user.service import (
    create_user,
    get_user,
    hash_user_password,
    update_user,
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
    def prepare_model(*, permissions=None, lang=None) -> UserCreate:
        rand = str(uuid4())
        model = UserCreate(
            first_name=f"John {rand}",
            last_name=f"Doe {rand}",
            email=f"john.doe_{rand}@example.net",  # noqa
            lang=lang or Lang.EN,
        )
        if permissions is not None:
            model.permissions = PermissionsInput.model_validate(permissions)
        return model

    @classmethod
    async def inject_into_db(
        cls, user: User = None, password="dummypassword"
    ) -> "PreparedUser":
        if user is None:
            user = cls.prepare_model()
        async with open_db_session() as session:
            user = await create_user(session, user)
            await update_user(session, user.id, UserUpdate(password=password))
        return cls(
            id=str(user.id),
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            },
            password=password,
        )

    async def expire_password_reset_token(self):
        async with open_db_session() as session:
            user_model = await get_user(session, UUID(self.id))
            user_model.password_reset_token_expires_at = datetime.now(
                timezone.utc
            ) - timedelta(days=1)
            await session.commit()

    @property
    def email(self) -> str:
        return self.data["email"]

    @property
    async def password_reset_token(self) -> str | None:
        async with open_db_session() as session:
            user_model = await get_user(session, UUID(self.id))
            return user_model.password_reset_token

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

    @staticmethod
    def build_expected_api_response(extra=None) -> dict:
        return {
            "id": callee.IsA(str),
            "lang": "en",
            "permissions": DEFAULT_PERMISSIONS,
            "authenticated_at": None,
            **(extra or {}),
        }

    def expected_api_response(self, extra=None) -> dict:
        return self.build_expected_api_response(
            {
                "id": self.id,
                "first_name": self.data["first_name"],
                "last_name": self.data["last_name"],
                "email": self.data["email"],
                "lang": self.data.get("lang", "en"),
                **(extra or {}),
            }
        )

    async def create_log_filter(self, data):
        async with self.client() as client:
            resp = await client.assert_post_created("/users/me/logs/filters", json=data)
        return PreparedLogFilter(resp.json()["id"], data)
