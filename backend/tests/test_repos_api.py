from datetime import datetime
from bson import ObjectId

import pytest
import callee


from helpers import assert_collection, ApiTestHelper

pytestmark = pytest.mark.anyio


class Test(ApiTestHelper):
    async def test_repo_create(self):
        resp = await self.post(
            "/repos", json={"name": "Repo 1"},
            expected_status_code=201
        )
        assert resp.json() == {"id": callee.IsA(str)}

        await assert_collection(
            self.db.repos,
            [{"_id": ObjectId(resp.json()["id"]), "name": "Repo 1", "created_at": callee.IsA(datetime)}]
        )

    async def test_repo_create_missing_name(self):
        await self.post(
            "/repos", json={},
            expected_status_code=422
        )
