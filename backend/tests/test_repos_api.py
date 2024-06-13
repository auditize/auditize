from datetime import datetime

import callee
import pytest
from icecream import ic
from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.database import DatabaseManager
from conftest import ApikeyBuilder, UserBuilder
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.logi18nprofiles import PreparedLogI18nProfile
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.repos import PreparedRepo
from helpers.utils import strip_dict_keys

pytestmark = pytest.mark.anyio


async def _test_repo_create(
    client: HttpTestHelper, dbm: DatabaseManager, collection: AsyncIOMotorCollection
):
    data = {"name": "myrepo"}

    resp = await client.assert_post(
        "/repos",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)},
    )
    repo = PreparedRepo(resp.json()["id"], data, dbm.core_db.repos)
    await assert_collection(dbm.core_db.repos, [repo.expected_document()])

    # check that the authenticated user has read & write permissions on the new repo
    permission_holder = await collection.find_one({})
    assert permission_holder["permissions"]["logs"]["repos"] == [
        {"repo_id": repo.id, "read": True, "write": True}
    ]


async def test_repo_create_as_apikey(
    apikey_builder: ApikeyBuilder, dbm: DatabaseManager
):
    apikey_builder = await apikey_builder({"management": {"repos": {"write": True}}})

    async with apikey_builder.client() as client:
        await _test_repo_create(client, dbm, dbm.core_db.apikeys)


async def test_repo_create_as_user(user_builder: UserBuilder, dbm: DatabaseManager):
    user_builder = await user_builder({"management": {"repos": {"write": True}}})

    async with user_builder.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_create(client, dbm, dbm.core_db.users)


@pytest.mark.parametrize("status", ["enabled", "readonly", "disabled"])
async def test_repo_create_with_explicit_status(
    superadmin_client: HttpTestHelper, dbm: DatabaseManager, status: str
):
    data = {"name": "myrepo", "status": status}

    resp = await superadmin_client.assert_post_created(
        "/repos",
        json=data,
        expected_json={"id": callee.IsA(str)},
    )
    repo = PreparedRepo(resp.json()["id"], data, dbm.core_db.repos)
    await assert_collection(dbm.core_db.repos, [repo.expected_document()])


async def test_repo_create_with_log_i18n_profile(
    superadmin_client: HttpTestHelper,
    dbm: DatabaseManager,
    log_i18n_profile: PreparedLogI18nProfile,
):
    data = {"name": "myrepo", "log_i18n_profile_id": log_i18n_profile.id}

    resp = await superadmin_client.assert_post_created(
        "/repos",
        json=data,
        expected_json={"id": callee.IsA(str)},
    )
    repo = PreparedRepo(resp.json()["id"], data, dbm.core_db.repos)
    await assert_collection(dbm.core_db.repos, [repo.expected_document()])


async def test_repo_create_missing_name(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await repo_write_client.assert_post_bad_request(
        "/repos",
        json={},
        expected_json={
            "message": "Invalid request",
            "validation_errors": [
                {
                    "field": "name",
                    "message": "Field required",
                }
            ],
        },
    )


async def test_repo_create_already_used_name(
    repo_write_client: HttpTestHelper, repo: PreparedRepo
):
    await repo_write_client.assert_post_constraint_violation(
        "/repos", json={"name": repo.data["name"]}
    )


async def test_repo_create_unknown_log_i18n_profile_id(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await repo_write_client.assert_post_bad_request(
        "/repos",
        json={"name": "myrepo", "log_i18n_profile_id": UNKNOWN_OBJECT_ID},
    )


async def test_repo_create_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_post_forbidden("/repos", json={"name": "myrepo"})


@pytest.mark.parametrize("field,value", [("name", "myrepo"), ("status", "disabled")])
async def test_repo_update(
    repo_write_client: HttpTestHelper,
    repo: PreparedRepo,
    dbm: DatabaseManager,
    field: str,
    value: str,
):
    await repo_write_client.assert_patch(
        f"/repos/{repo.id}", json={field: value}, expected_status_code=204
    )

    await assert_collection(dbm.core_db.repos, [repo.expected_document({field: value})])


async def test_repo_update_set_log_i18n_profile_id(
    repo_write_client: HttpTestHelper,
    repo: PreparedRepo,
    log_i18n_profile: PreparedLogI18nProfile,
    dbm: DatabaseManager,
):
    await repo_write_client.assert_patch_no_content(
        f"/repos/{repo.id}",
        json={"log_i18n_profile_id": log_i18n_profile.id},
    )
    await assert_collection(
        dbm.core_db.repos,
        [repo.expected_document({"log_i18n_profile_id": log_i18n_profile.id})],
    )


async def test_repo_update_unset_log_i18n_profile_id(
    repo_write_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
    dbm: DatabaseManager,
):
    repo = await PreparedRepo.create(
        dbm, {"name": "repo", "log_i18n_profile_id": log_i18n_profile.id}
    )
    repo: PreparedRepo  # make pycharm happy
    await repo_write_client.assert_patch_no_content(
        f"/repos/{repo.id}",
        json={"log_i18n_profile_id": None},
    )
    await assert_collection(
        dbm.core_db.repos,
        [repo.expected_document({"log_i18n_profile_id": None})],
    )


async def test_repo_update_empty_with_log_i18n_profile_id_already_set(
    repo_write_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
    dbm: DatabaseManager,
):
    repo = await PreparedRepo.create(
        dbm, {"name": "repo", "log_i18n_profile_id": log_i18n_profile.id}
    )
    repo: PreparedRepo  # make pycharm happy
    await repo_write_client.assert_patch_no_content(
        f"/repos/{repo.id}",
        json={},
    )
    await assert_collection(dbm.core_db.repos, [repo.expected_document()])


async def test_repo_update_unknown_id(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_patch_not_found(
        f"/repos/{UNKNOWN_OBJECT_ID}",
        json={"name": "Repo Updated"},
    )


async def test_repo_update_already_used_name(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    repo1 = await PreparedRepo.create(dbm)
    repo2 = await PreparedRepo.create(dbm)

    await repo_write_client.assert_patch_constraint_violation(
        f"/repos/{repo1.id}",
        json={"name": repo2.data["name"]},
    )


async def test_repo_update_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_patch_forbidden(
        f"/repos/{repo.id}", json={"name": "Repo Updated"}
    )


async def test_repo_get(repo_read_client: HttpTestHelper, repo: PreparedRepo):
    await repo_read_client.assert_get(
        f"/repos/{repo.id}",
        expected_status_code=200,
        expected_json=repo.expected_api_response(),
    )


async def test_repo_get_with_stats_empty(
    repo_read_client: HttpTestHelper, repo: PreparedRepo
):
    await repo_read_client.assert_get(
        f"/repos/{repo.id}?include=stats",
        expected_status_code=200,
        expected_json=repo.expected_api_response(
            {
                "stats": {
                    "first_log_date": None,
                    "last_log_date": None,
                    "log_count": 0,
                    "storage_size": callee.IsA(int),
                }
            }
        ),
    )


async def test_repo_get_with_stats(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log(
        superadmin_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    await repo.create_log(
        superadmin_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await superadmin_client.assert_get(
        f"/repos/{repo.id}?include=stats",
        expected_status_code=200,
        expected_json=repo.expected_api_response(
            {
                "stats": {
                    "first_log_date": "2024-01-01T00:00:00Z",
                    "last_log_date": "2024-01-02T00:00:00Z",
                    "log_count": 2,
                    "storage_size": callee.IsA(int),
                }
            }
        ),
    )


async def test_repo_get_unknown_id(
    repo_read_client: HttpTestHelper, dbm: DatabaseManager
):
    await repo_read_client.assert_get_not_found(f"/repos/{UNKNOWN_OBJECT_ID}")


async def test_repo_get_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}")


async def test_repo_list(repo_read_client: HttpTestHelper, dbm: DatabaseManager):
    repos = [await PreparedRepo.create(dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        repo_read_client,
        "/repos",
        [
            repo.expected_api_response()
            for repo in sorted(repos, key=lambda r: r.data["name"])
        ],
    )


async def test_repo_list_with_search(
    repo_read_client: HttpTestHelper, dbm: DatabaseManager
):
    repos = [await PreparedRepo.create(dbm, {"name": f"repo_{i}"}) for i in range(2)]

    await repo_read_client.assert_get_ok(
        "/repos?q=repo_1",
        expected_json={
            "items": [repos[1].expected_api_response()],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_repo_list_with_stats(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log(
        superadmin_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00.123Z")
    )

    await superadmin_client.assert_get(
        f"/repos?include=stats",
        expected_status_code=200,
        expected_json={
            "items": [
                repo.expected_api_response(
                    {
                        "stats": {
                            "first_log_date": "2024-01-01T00:00:00Z",
                            "last_log_date": "2024-01-01T00:00:00Z",
                            "log_count": 1,
                            "storage_size": callee.IsA(int),
                        }
                    }
                )
            ],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_repo_list_all_statuses(
    superadmin_client: HttpTestHelper, dbm: DatabaseManager
):
    repos = []
    for i, status in enumerate(("enabled", "readonly", "disabled")):
        repo: PreparedRepo = await PreparedRepo.create(
            dbm, {"name": f"repo_{i}", "status": status}
        )
        repos.append(repo)

    await superadmin_client.assert_get_ok(
        "/repos",
        expected_json={
            "items": [repo.expected_api_response() for repo in repos],
            "pagination": {"page": 1, "page_size": 10, "total": 3, "total_pages": 1},
        },
    )


async def test_repo_list_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_get_forbidden("/repos")


async def test_repo_list_user_repos_simple(
    user_builder: UserBuilder, repo: PreparedRepo
):
    # some very basic test to ensure that the response is properly shaped
    # we'll test the permissions in a separate test

    user = await user_builder({"is_superadmin": True})

    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get_ok(
            "/users/me/repos",
            expected_json={
                "items": [
                    strip_dict_keys(
                        repo.expected_api_response(
                            {"permissions": {"read_logs": True, "write_logs": True}}
                        ),
                        "status",
                        "created_at",
                        "stats",
                        "log_i18n_profile_id",
                    )
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 1,
                    "total_pages": 1,
                },
            },
        )


async def _test_repo_list_user_repos(
    client: HttpTestHelper, params: dict, expected: dict[str, dict]
):
    resp = await client.assert_get_ok(
        "/users/me/repos",
        params=params,
    )
    items = resp.json()["items"]
    assert len(items) == len(expected)
    for expected_repo, expected_repo_perms in expected.items():
        ic(expected_repo, expected_repo_perms)
        assert any(
            repo["id"] == expected_repo and repo["permissions"] == expected_repo_perms
            for repo in items
        )


async def test_repo_list_user_repos_with_permissions(
    user_builder: UserBuilder, dbm: DatabaseManager
):
    repo_1 = await PreparedRepo.create(dbm, {"name": "repo_1"})
    repo_2 = await PreparedRepo.create(dbm, {"name": "repo_2"})
    repo_3 = await PreparedRepo.create(dbm, {"name": "repo_3"})
    repo_readonly = await PreparedRepo.create(
        dbm, {"name": "repo_readonly", "status": "readonly"}
    )
    repo_disabled = await PreparedRepo.create(
        dbm, {"name": "repo_disabled", "status": "disabled"}
    )

    # Test #1 with user having read&write permissions on all repos
    user = await user_builder({"logs": {"read": True, "write": True}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {
                repo_1.id: {"read_logs": True, "write_logs": True},
                repo_2.id: {"read_logs": True, "write_logs": True},
                repo_3.id: {"read_logs": True, "write_logs": True},
                repo_readonly.id: {"read_logs": True, "write_logs": False},
            },
        )

    # Test #2 with user having specific permissions on various repos
    user = await user_builder(
        {
            "logs": {
                "repos": [
                    {"repo_id": repo_1.id, "read": True, "write": False},
                    {"repo_id": repo_2.id, "read": False, "write": True},
                    {"repo_id": repo_3.id, "read": True, "write": True},
                    {"repo_id": repo_readonly.id, "read": True, "write": True},
                    {"repo_id": repo_disabled.id, "read": True, "write": True},
                ]
            }
        }
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {
                repo_1.id: {"read_logs": True, "write_logs": False},
                repo_2.id: {"read_logs": False, "write_logs": True},
                repo_3.id: {"read_logs": True, "write_logs": True},
                repo_readonly.id: {"read_logs": True, "write_logs": False},
            },
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True},
            {
                repo_1.id: {"read_logs": True, "write_logs": False},
                repo_3.id: {"read_logs": True, "write_logs": True},
                repo_readonly.id: {"read_logs": True, "write_logs": False},
            },
        )
        await _test_repo_list_user_repos(
            client,
            {"has_write_permission": True},
            {
                repo_2.id: {"read_logs": False, "write_logs": True},
                repo_3.id: {"read_logs": True, "write_logs": True},
            },
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True, "has_write_permission": True},
            {repo_3.id: {"read_logs": True, "write_logs": True}},
        )

    # Test #3 with user having no log permissions (but can manage repos)
    user = await user_builder({"management": {"repos": {"read": True, "write": True}}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {},  # no repo should be returned
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True},
            {},  # no repo should be returned
        )


async def test_repo_list_user_repos_unauthorized(anon_client: HttpTestHelper):
    # /users/me/repos does not require any permission (as its job is to
    # return authorized repos for log access)
    # but the user must be authenticated
    await anon_client.assert_get_unauthorized("/users/me/repos")


async def test_repo_list_user_repos_as_apikey(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({"is_superadmin": True})
    async with apikey.client() as client:
        await client.assert_get_forbidden("/users/me/repos")


async def test_repo_delete(
    repo_write_client: HttpTestHelper, repo: PreparedRepo, dbm: DatabaseManager
):
    await repo_write_client.assert_delete(f"/repos/{repo.id}", expected_status_code=204)

    await assert_collection(dbm.core_db.repos, [])


async def test_repo_delete_unknown_id(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await repo_write_client.assert_delete_not_found(f"/repos/{UNKNOWN_OBJECT_ID}")


async def test_repo_delete_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_delete_forbidden(f"/repos/{repo.id}")
