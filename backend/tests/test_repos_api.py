import uuid
from datetime import datetime
from bson import ObjectId

import pytest
import callee
from httpx import AsyncClient

from auditize.common.mongo import DatabaseManager

from helpers import UNKNOWN_LOG_ID, assert_post, assert_get, assert_patch, \
    assert_delete, assert_collection, do_test_page_pagination_common_scenarios

pytestmark = pytest.mark.anyio


def prepare_repo_data(extra=None):
    return {
        "name": f"Repo {uuid.uuid4()}",
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

    def expected_response(self):
        return {
            "id": self.id,
            "name": self.data["name"],
            "created_at": callee.IsA(str)
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


async def test_repo_create(client: AsyncClient, dbm: DatabaseManager):
    data = prepare_repo_data()
    resp = await assert_post(
        client,
        "/repos", json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)}
    )

    repo = PreparedRepo(resp.json()["id"], data)
    await assert_collection(dbm.core_db.repos, [repo.expected_document()])


async def test_repo_create_missing_name(client: AsyncClient, dbm: DatabaseManager):
    await assert_post(
        client,
        "/repos", json={},
        expected_status_code=422
    )


async def test_repo_create_already_used_name(client: AsyncClient, dbm: DatabaseManager):
    repo = await prepare_repo(client)

    await assert_post(
        client,
        "/repos", json={"name": repo.data["name"]},
        expected_status_code=409
    )


async def test_repo_update(client: AsyncClient, dbm: DatabaseManager):
    repo = await prepare_repo(client)

    await assert_patch(
        client,
        f"/repos/{repo.id}", json={"name": "Repo Updated"},
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.repos, [repo.expected_document({"name": "Repo Updated"})])


async def test_repo_update_unknown_id(client: AsyncClient):
    await assert_patch(
        client,
        f"/repos/{UNKNOWN_LOG_ID}", json={"name": "Repo Updated"},
        expected_status_code=404
    )


async def test_repo_update_already_used_name(client: AsyncClient, dbm: DatabaseManager):
    repo1 = await prepare_repo(client)
    repo2 = await prepare_repo(client)

    await assert_patch(
        client,
        f"/repos/{repo1.id}", json={"name": repo2.data["name"]},
        expected_status_code=409
    )


async def test_repo_get(client: AsyncClient, dbm: DatabaseManager):
    repo = await prepare_repo(client)

    await assert_get(
        client, f"/repos/{repo.id}",
        expected_status_code=200,
        expected_json=repo.expected_response()
    )


async def test_repo_get_unknown_id(client: AsyncClient, dbm: DatabaseManager):
    await assert_get(
        client,
        f"/repos/{UNKNOWN_LOG_ID}",
        expected_status_code=404
    )


async def test_repo_list(client: AsyncClient, dbm: DatabaseManager):
    repos = [await prepare_repo(client) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        client, "/repos",
        [repo.expected_response() for repo in repos]
    )


async def test_repo_delete(client: AsyncClient, dbm: DatabaseManager):
    repo = await prepare_repo(client)

    await assert_delete(
        client,
        f"/repos/{repo.id}",
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.repos, [])


async def test_repo_delete_unknown_id(client: AsyncClient, dbm: DatabaseManager):
    await assert_delete(
        client,
        f"/repos/{UNKNOWN_LOG_ID}",
        expected_status_code=404
    )
