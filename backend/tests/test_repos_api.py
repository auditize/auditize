from datetime import datetime
from bson import ObjectId

import pytest
import callee
from httpx import AsyncClient

from auditize.common.mongo import Database

from helpers import assert_post, assert_collection

pytestmark = pytest.mark.anyio


async def test_repo_create(client: AsyncClient, db: Database):
    resp = await assert_post(
        client,
        "/repos", json={"name": "Repo 1"},
        expected_status_code=201
    )
    assert resp.json() == {"id": callee.IsA(str)}

    await assert_collection(
        db.repos,
        [{"_id": ObjectId(resp.json()["id"]), "name": "Repo 1", "created_at": callee.IsA(datetime)}]
    )


async def test_repo_create_missing_name(client: AsyncClient, db: Database):
    await assert_post(
        client,
        "/repos", json={},
        expected_status_code=422
    )
