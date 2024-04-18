import uuid
from datetime import datetime
from bson import ObjectId

import pytest
import callee

from auditize.common.mongo import DatabaseManager

from helpers import (
    UNKNOWN_LOG_ID, assert_collection, do_test_page_pagination_common_scenarios,
    prepare_log, alter_log_saved_at
)
from helpers.http import HttpTestHelper
from helpers.repos import RepoTestHelper

pytestmark = pytest.mark.anyio


async def test_repo_create(client: HttpTestHelper, dbm: DatabaseManager):
    data = RepoTestHelper.prepare_data()
    resp = await client.assert_post(
        "/repos", json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)}
    )

    repo = RepoTestHelper(resp.json()["id"], data, dbm.core_db.repos)
    await assert_collection(dbm.core_db.repos, [repo.expected_document()])


async def test_repo_create_missing_name(client: HttpTestHelper, dbm: DatabaseManager):
    await client.assert_post(
        "/repos", json={},
        expected_status_code=422
    )


async def test_repo_create_already_used_name(client: HttpTestHelper, repo: RepoTestHelper):
    await client.assert_post(
        "/repos", json={"name": repo.data["name"]},
        expected_status_code=409
    )


async def test_repo_update(client: HttpTestHelper, repo: RepoTestHelper, dbm: DatabaseManager):
    await client.assert_patch(
        f"/repos/{repo.id}", json={"name": "Repo Updated"},
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.repos, [repo.expected_document({"name": "Repo Updated"})])


async def test_repo_update_unknown_id(client: HttpTestHelper):
    await client.assert_patch(
        f"/repos/{UNKNOWN_LOG_ID}", json={"name": "Repo Updated"},
        expected_status_code=404
    )


async def test_repo_update_already_used_name(client: HttpTestHelper, dbm: DatabaseManager):
    repo1 = await RepoTestHelper.create(dbm)
    repo2 = await RepoTestHelper.create(dbm)

    await client.assert_patch(
        f"/repos/{repo1.id}", json={"name": repo2.data["name"]},
        expected_status_code=409
    )


async def test_repo_get(client: HttpTestHelper, repo: RepoTestHelper):
    await client.assert_get(
        f"/repos/{repo.id}",
        expected_status_code=200,
        expected_json=repo.expected_api_response()
    )


async def test_repo_get_with_stats_empty(client: HttpTestHelper, repo: RepoTestHelper):
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


async def test_repo_get_with_stats(client: HttpTestHelper, repo: RepoTestHelper):
    log1_id = await prepare_log(client, repo.id)
    alter_log_saved_at(repo.db, log1_id, datetime.fromisoformat("2024-01-01T00:00:00Z"))
    log2_id = await prepare_log(client, repo.id)
    alter_log_saved_at(repo.db, log2_id, datetime.fromisoformat("2024-01-02T00:00:00Z"))

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
        f"/repos/{UNKNOWN_LOG_ID}",
        expected_status_code=404
    )


async def test_repo_list(client: HttpTestHelper, dbm: DatabaseManager):
    repos = [await RepoTestHelper.create(dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        client, "/repos",
        [repo.expected_api_response() for repo in sorted(repos, key=lambda r: r.data["name"])]
    )


async def test_repo_list_with_stats(client: HttpTestHelper, repo: RepoTestHelper):
    log_id = await prepare_log(client, repo.id)
    alter_log_saved_at(repo.db, log_id, datetime.fromisoformat("2024-01-01T00:00:00Z"))

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


async def test_repo_delete(client: HttpTestHelper, repo: RepoTestHelper, dbm: DatabaseManager):
    await client.assert_delete(
        f"/repos/{repo.id}",
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.repos, [])


async def test_repo_delete_unknown_id(client: HttpTestHelper, dbm: DatabaseManager):
    await client.assert_delete(
        f"/repos/{UNKNOWN_LOG_ID}",
        expected_status_code=404
    )
