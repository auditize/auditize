from datetime import datetime
from bson import ObjectId

import pytest
import callee
from httpx import AsyncClient

from auditize.common.mongo import Database

from helpers import UNKNOWN_LOG_ID, assert_post, assert_patch, assert_collection

pytestmark = pytest.mark.anyio


def prepare_repo_data(extra=None):
    return {
        "name": "Repo 1",
        **(extra or {})
    }


class PreparedRepo:
    def __init__(self, id, data):
        self.id = id
        self.data = data

    def expected_document(self, extra=None):
        return {
            "_id": ObjectId(self.id),
            "name": self.data["name"],
            "created_at": callee.IsA(datetime),
            **(extra or {})
        }


async def prepare_repo(client: AsyncClient, data=None) -> PreparedRepo:
    if data is None:
        data = prepare_repo_data()
    resp = await assert_post(
        client,
        "/repos", json=data,
        expected_status_code=201
    )
    return PreparedRepo(resp.json()["id"], data)


async def test_repo_create(client: AsyncClient, db: Database):
    data = prepare_repo_data()
    resp = await assert_post(
        client,
        "/repos", json=data,
        expected_status_code=201
    )
    assert resp.json() == {"id": callee.IsA(str)}

    repo = PreparedRepo(resp.json()["id"], data)
    await assert_collection(db.repos, [repo.expected_document()])


async def test_repo_create_missing_name(client: AsyncClient, db: Database):
    await assert_post(
        client,
        "/repos", json={},
        expected_status_code=422
    )


async def test_repo_update(client: AsyncClient, db: Database):
    repo = await prepare_repo(client)

    await assert_patch(
        client,
        f"/repos/{repo.id}", json={"name": "Repo Updated"},
        expected_status_code=204
    )

    await assert_collection(db.repos, [repo.expected_document({"name": "Repo Updated"})])


async def test_repo_update_unknown_id(client: AsyncClient):
    await assert_patch(
        client,
        f"/repos/{UNKNOWN_LOG_ID}", json={"name": "Repo Updated"},
        expected_status_code=404
    )
