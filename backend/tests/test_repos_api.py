from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection

import pytest
import callee
from icecream import ic

from auditize.common.db import DatabaseManager

from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.database import assert_collection
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.http import HttpTestHelper
from helpers.repos import PreparedRepo
from tests.helpers.integrations import PreparedIntegration
from conftest import IntegrationBuilder, UserBuilder

pytestmark = pytest.mark.anyio


async def _test_repo_create(client: HttpTestHelper, dbm: DatabaseManager, collection: AsyncIOMotorCollection):
    data = {"name": "myrepo"}

    resp = await client.assert_post(
        "/repos", json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)}
    )
    repo = PreparedRepo(resp.json()["id"], data, dbm.core_db.repos)
    await assert_collection(dbm.core_db.repos, [repo.expected_document()])

    # check that the authenticated user has read & write permissions on the new repo
    permission_holder = await collection.find_one({})
    assert permission_holder["permissions"]["logs"]["repos"] == {repo.id: {"read": True, "write": True}}


async def test_repo_create_as_integration(integration_builder: IntegrationBuilder, dbm: DatabaseManager):
    integration_builder = await integration_builder({"entities": {"repos": {"write": True}}})

    async with integration_builder.client() as client:
        await _test_repo_create(client, dbm, dbm.core_db.integrations)


async def test_repo_create_as_user(user_builder: UserBuilder, dbm: DatabaseManager):
    user_builder = await user_builder({"entities": {"repos": {"write": True}}})

    async with user_builder.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_create(client, dbm, dbm.core_db.users)


async def test_repo_create_missing_name(client: HttpTestHelper, dbm: DatabaseManager):
    await client.assert_post(
        "/repos", json={},
        expected_status_code=422
    )


async def test_repo_create_already_used_name(client: HttpTestHelper, repo: PreparedRepo):
    await client.assert_post(
        "/repos", json={"name": repo.data["name"]},
        expected_status_code=409
    )


async def test_repo_create_unauthorized(anon_client: HttpTestHelper):
    await anon_client.assert_unauthorized_post(
        "/repos", json={"name": "myrepo"}
    )


async def test_repo_update(client: HttpTestHelper, repo: PreparedRepo, dbm: DatabaseManager):
    await client.assert_patch(
        f"/repos/{repo.id}", json={"name": "Repo Updated"},
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.repos, [repo.expected_document({"name": "Repo Updated"})])


async def test_repo_update_unknown_id(client: HttpTestHelper):
    await client.assert_patch(
        f"/repos/{UNKNOWN_OBJECT_ID}", json={"name": "Repo Updated"},
        expected_status_code=404
    )


async def test_repo_update_already_used_name(client: HttpTestHelper, dbm: DatabaseManager):
    repo1 = await PreparedRepo.create(dbm)
    repo2 = await PreparedRepo.create(dbm)

    await client.assert_patch(
        f"/repos/{repo1.id}", json={"name": repo2.data["name"]},
        expected_status_code=409
    )


async def test_repo_update_unauthorized(anon_client: HttpTestHelper, repo: PreparedRepo):
    await anon_client.assert_unauthorized_patch(
        f"/repos/{repo.id}", json={"name": "Repo Updated"}
    )


async def test_repo_get(client: HttpTestHelper, repo: PreparedRepo):
    await client.assert_get(
        f"/repos/{repo.id}",
        expected_status_code=200,
        expected_json=repo.expected_api_response()
    )


async def test_repo_get_with_stats_empty(client: HttpTestHelper, repo: PreparedRepo):
    await client.assert_get(
        f"/repos/{repo.id}?include=stats",
        expected_status_code=200,
        expected_json=repo.expected_api_response({
            "stats": {
                "first_log_date": None,
                "last_log_date": None,
                "log_count": 0,
                "storage_size": callee.IsA(int)
            }
        })
    )


async def test_repo_get_with_stats(client: HttpTestHelper, repo: PreparedRepo):
    await repo.create_log(client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"))
    await repo.create_log(client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z"))

    await client.assert_get(
        f"/repos/{repo.id}?include=stats",
        expected_status_code=200,
        expected_json=repo.expected_api_response({
            "stats": {
                "first_log_date": "2024-01-01T00:00:00Z",
                "last_log_date": "2024-01-02T00:00:00Z",
                "log_count": 2,
                "storage_size": callee.IsA(int)
            }
        })
    )


async def test_repo_get_unknown_id(client: HttpTestHelper, dbm: DatabaseManager):
    await client.assert_get(
        f"/repos/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )


async def test_repo_get_unauthorized(anon_client: HttpTestHelper, repo: PreparedRepo):
    await anon_client.assert_unauthorized_get(
        f"/repos/{repo.id}"
    )


async def test_repo_list(client: HttpTestHelper, dbm: DatabaseManager):
    repos = [await PreparedRepo.create(dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        client, "/repos",
        [repo.expected_api_response() for repo in sorted(repos, key=lambda r: r.data["name"])]
    )


async def test_repo_list_with_stats(client: HttpTestHelper, repo: PreparedRepo):
    await repo.create_log(client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"))

    await client.assert_get(
        f"/repos?include=stats",
        expected_status_code=200,
        expected_json={
            "data": [
                repo.expected_api_response({
                    "stats": {
                        "first_log_date": "2024-01-01T00:00:00Z",
                        "last_log_date": "2024-01-01T00:00:00Z",
                        "log_count": 1,
                        "storage_size": callee.IsA(int)
                    }
                })
            ],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 1,
                "total_pages": 1
            }
        }
    )


async def _test_repo_list_user_repos(client: HttpTestHelper, params: dict, expected: dict[str, dict]):
    resp = await client.assert_get(
        "/users/me/repos", params=params,
        expected_status_code=200,
    )
    data = resp.json()["data"]
    assert len(expected) == len(data)
    for expected_repo, expected_repo_perms in expected.items():
        ic(expected_repo, expected_repo_perms)
        assert any(
            repo["id"] == expected_repo and repo["permissions"] == expected_repo_perms
            for repo in data
        )


async def test_repo_list_user_repos(user_builder: UserBuilder, dbm: DatabaseManager):
    repo_1 = await PreparedRepo.create(dbm, {"name": "repo_1"})
    repo_2 = await PreparedRepo.create(dbm, {"name": "repo_2"})
    repo_3 = await PreparedRepo.create(dbm, {"name": "repo_3"})

    user = await user_builder({"logs": {"read": True, "write": True}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {
                repo_1.id: {"read_logs": True, "write_logs": True},
                repo_2.id: {"read_logs": True, "write_logs": True},
                repo_3.id: {"read_logs": True, "write_logs": True}
            }
        )

    user = await user_builder({
        "logs": {
            "repos": {
                repo_1.id: {"read": True, "write": False},
                repo_2.id: {"read": False, "write": True},
                repo_3.id: {"read": True, "write": True}
            }
        }
    })
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {
                repo_1.id: {"read_logs": True, "write_logs": False},
                repo_2.id: {"read_logs": False, "write_logs": True},
                repo_3.id: {"read_logs": True, "write_logs": True}
            }
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True},
            {
                repo_1.id: {"read_logs": True, "write_logs": False},
                repo_3.id: {"read_logs": True, "write_logs": True}
            }
        )
        await _test_repo_list_user_repos(
            client,
            {"has_write_permission": True},
            {
                repo_2.id: {"read_logs": False, "write_logs": True},
                repo_3.id: {"read_logs": True, "write_logs": True}
            }
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True, "has_write_permission": True},
            {
                repo_3.id: {"read_logs": True, "write_logs": True}
            }
        )


async def test_repo_list_unauthorized(anon_client: HttpTestHelper):
    await anon_client.assert_unauthorized_get(
        "/repos"
    )


async def test_repo_delete(client: HttpTestHelper, repo: PreparedRepo, dbm: DatabaseManager):
    await client.assert_delete(
        f"/repos/{repo.id}",
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.repos, [])


async def test_repo_delete_unknown_id(client: HttpTestHelper, dbm: DatabaseManager):
    await client.assert_delete(
        f"/repos/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )


async def test_repo_delete_unauthorized(anon_client: HttpTestHelper, repo: PreparedRepo):
    await anon_client.assert_unauthorized_delete(
        f"/repos/{repo.id}"
    )
