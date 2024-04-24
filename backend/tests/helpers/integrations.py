from datetime import datetime
import uuid
from bson import ObjectId

import callee

from auditize.common.db import DatabaseManager

from .http import HttpTestHelper


class PreparedIntegration:
    def __init__(self, id: str, token: str, data: dict, dbm: DatabaseManager):
        self.id = id
        self.token = token
        self.data = data
        self.dbm = dbm

    @staticmethod
    def prepare_data(extra=None):
        return {
            "name": f"Integration {uuid.uuid4()}",
            **(extra or {})
        }

    @classmethod
    async def create(cls, client: HttpTestHelper, dbm: DatabaseManager):
        data = cls.prepare_data()
        resp = await client.assert_post(
            "/integrations", json=data,
            expected_status_code=201,
        )
        return cls(resp.json()["id"], resp.json()["token"], data, dbm)

    def expected_document(self, extra=None):
        return {
            "_id": ObjectId(self.id),
            "name": self.data["name"],
            "token_hash": callee.IsA(str),
            "created_at": callee.IsA(datetime),
            **(extra or {})
        }

    def expected_api_response(self, extra=None):
        return {
            "id": self.id,
            "name": self.data["name"],
            **(extra or {})
        }
