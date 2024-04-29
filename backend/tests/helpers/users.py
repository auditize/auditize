import uuid
from datetime import datetime, timedelta, timezone
from bson import ObjectId

from httpx import Response
import callee

from auditize.common.db import DatabaseManager
from auditize.users.service import get_user, hash_user_password
from auditize.users.models import User

from .http import HttpTestHelper, get_cookie_by_name, create_http_client


class PreparedUser:
    def __init__(self, id: str, data: dict, dbm: DatabaseManager, password=None):
        self.id = id
        self.data = data
        self.dbm = dbm
        self.password = password

    @staticmethod
    def prepare_data(extra=None):
        rand = str(uuid.uuid4())
        return {
            "first_name": f"John {rand}",
            "last_name": f"Doe {rand}",
            "email": f"john.doe_{rand}@example.net",
            **(extra or {})
        }

    @classmethod
    async def create(cls, client: HttpTestHelper, dbm: DatabaseManager) -> "PreparedUser":
        data = cls.prepare_data()
        resp = await client.assert_post(
            "/users", json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], data, dbm)

    @staticmethod
    def prepare_model(password="dummypassword") -> User:
        rand = str(uuid.uuid4())
        return User(
            first_name=f"John {rand}",
            last_name=f"Doe {rand}",
            email=f"john.doe_{rand}@example.net",
            password_hash=hash_user_password(password)
        )

    @classmethod
    async def inject_into_db(cls, dbm: DatabaseManager, user: User = None) -> "PreparedUser":
        password = None
        if user is None:
            password = "dummypassword"
            user = cls.prepare_model(password=password)
        result = await dbm.core_db.users.insert_one(user.model_dump())
        return cls(
            id=str(result.inserted_id),
            data={
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            },
            password=password,
            dbm=dbm
        )

    async def expire_signup_token(self):
        await self.dbm.core_db.users.update_one(
            {"_id": ObjectId(self.id)},
            {"$set": {"signup_token.expires_at": datetime.now(timezone.utc) - timedelta(days=1)}}
        )

    @property
    def email(self) -> str:
        return self.data["email"]

    @property
    async def signup_token(self) -> str | None:
        user_model = await get_user(self.dbm, self.id)
        return user_model.signup_token.token if user_model.signup_token else None

    async def log_in(self, client: HttpTestHelper) -> Response:
        return await client.assert_post(
            "/users/login", json={"email": self.email, "password": self.password},
            expected_status_code=204
        )

    async def client(self) -> HttpTestHelper:
        client = create_http_client()
        await self.log_in(client)
        return client

    async def get_session_token(self, client: HttpTestHelper) -> str:
        resp = await self.log_in(client)
        return get_cookie_by_name(resp, "session").value

    def expected_document(self, extra=None) -> dict:
        return {
            "_id": ObjectId(self.id),
            "first_name": self.data["first_name"],
            "last_name": self.data["last_name"],
            "email": self.data["email"],
            "password_hash": None,
            "created_at": callee.IsA(datetime),
            "signup_token": {
                "token": callee.Regex(r"^[0-9a-f]{64}$"),
                "expires_at": callee.IsA(datetime),
            },
            **(extra or {})
        }

    def expected_api_response(self, extra=None) -> dict:
        return {
            "id": self.id,
            "first_name": self.data["first_name"],
            "last_name": self.data["last_name"],
            "email": self.data["email"],
            **(extra or {})
        }
