import uuid
from datetime import datetime
from bson import ObjectId

import callee

from .http import HttpTestHelper


class PreparedUser:
    def __init__(self, id: str, data: dict):
        self.id = id
        self.data = data

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
    async def create(cls, client: HttpTestHelper):
        data = cls.prepare_data()
        resp = await client.assert_post(
            "/users", json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], data)

    def expected_document(self, extra=None):
        return {
            "_id": ObjectId(self.id),
            "first_name": self.data["first_name"],
            "last_name": self.data["last_name"],
            "email": self.data["email"],
            "password_hash": None,
            "created_at": callee.IsA(datetime),
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
