import uuid
from datetime import datetime, timedelta, timezone
from bson import ObjectId

import callee

from auditize.common.db import DatabaseManager
from auditize.users.service import get_user

from .http import HttpTestHelper


class PreparedUser:
    def __init__(self, id: str, data: dict, dbm: DatabaseManager):
        self.id = id
        self.data = data
        self.dbm = dbm

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
    async def create(cls, client: HttpTestHelper, dbm: DatabaseManager):
        data = cls.prepare_data()
        resp = await client.assert_post(
            "/users", json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], data, dbm)

    async def expire_signup_token(self):
        await self.dbm.core_db.users.update_one(
            {"_id": ObjectId(self.id)},
            {"$set": {"signup_token.expires_at": datetime.now(timezone.utc) - timedelta(days=1)}}
        )

    @property
    async def signup_token(self):
        user_model = await get_user(self.dbm, self.id)
        return user_model.signup_token.token if user_model.signup_token else None

    def expected_document(self, extra=None):
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

    def expected_api_response(self, extra=None):
        return {
            "id": self.id,
            "first_name": self.data["first_name"],
            "last_name": self.data["last_name"],
            "email": self.data["email"],
            **(extra or {})
        }
