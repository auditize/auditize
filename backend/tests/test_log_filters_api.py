from typing import Any
from uuid import UUID

import callee
import pytest

from auditize.database import DatabaseManager
from conftest import RepoBuilder, UserBuilder
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.logfilters import DEFAULT_SEARCH_PARAMETERS, PreparedLogFilter
from helpers.logs import UNKNOWN_UUID
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.repo import PreparedRepo
from helpers.user import PreparedUser

pytestmark = pytest.mark.anyio


async def _test_log_filter_creation(
    user: PreparedUser, data: dict, dbm: DatabaseManager
):
    async with user.client() as client:
        client: HttpTestHelper
        resp = await client.assert_post_created(
            "/users/me/logs/filters",
            json=data,
            expected_json={"id": callee.IsA(str)},
        )

    log_filter = PreparedLogFilter(resp.json()["id"], data)

    await assert_collection(
        dbm.core_db.log_filters,
        [log_filter.expected_document({"user_id": UUID(user.id)})],
    )


async def test_log_filter_create_simple(
    log_read_user: PreparedUser, repo: PreparedRepo, dbm: DatabaseManager
):
    await _test_log_filter_creation(
        log_read_user,
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {"action_type": "some action"},
            "columns": [
                "saved_at",
                "action_type",
            ],
        },
        dbm,
    )


async def test_log_filter_create_all_builtin_field_search_parameters(
    log_read_user: PreparedUser, repo: PreparedRepo, dbm: DatabaseManager
):
    params: dict[str, Any] = {k: "some value" for k in DEFAULT_SEARCH_PARAMETERS}
    params["since"] = "2021-01-01T00:00:00Z"
    params["until"] = "2021-01-02T00:00:00Z"
    params["has_attachment"] = True
    await _test_log_filter_creation(
        log_read_user,
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": params,
            "columns": [],
        },
        dbm,
    )


async def test_log_filter_create_all_custom_field_search_parameters(
    log_read_user: PreparedUser, repo: PreparedRepo, dbm: DatabaseManager
):
    await _test_log_filter_creation(
        log_read_user,
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {
                "actor.custom_actor_field": "actor field",
                "resource.custom_resource_field": "resource field",
                "source.custom_source_field": "source field",
                "details.custom_details_field": "details field",
            },
            "columns": [],
        },
        dbm,
    )


async def test_log_filter_create_all_builtin_field_columns(
    log_read_user: PreparedUser, repo: PreparedRepo, dbm: DatabaseManager
):
    await _test_log_filter_creation(
        log_read_user,
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {},
            "columns": [
                "saved_at",
                "action",
                "action_type",
                "action_category",
                "actor",
                "actor_ref",
                "actor_type",
                "actor_name",
                "resource",
                "resource_ref",
                "resource_type",
                "resource_name",
                "tag",
                "tag_ref",
                "tag_type",
                "tag_name",
                "attachment",
                "attachment_name",
                "attachment_type",
                "attachment_mime_type",
                "node",
            ],
        },
        dbm,
    )


async def test_log_filter_create_all_custom_field_columns(
    log_read_user: PreparedUser, repo: PreparedRepo, dbm: DatabaseManager
):
    await _test_log_filter_creation(
        log_read_user,
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {},
            "columns": [
                "actor.custom_actor_field"
                "resource.custom_resource_field"
                "source.custom_source_field"
                "details.custom_details_field"
            ],
        },
        dbm,
    )


async def test_log_filter_create_missing_param(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    template = {
        "name": "my filter",
        "repo_id": repo.id,
        "search_params": {"action_type": "some action"},
        "columns": [
            "saved_at",
            "action_type",
        ],
    }
    async with log_read_user.client() as client:
        client: HttpTestHelper
        for key in template:
            data = template.copy()
            del data[key]
            await client.assert_post_bad_request("/users/me/logs/filters", json=data)


async def test_log_filter_create_invalid_search_param_builtin_field(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_post_bad_request(
            "/users/me/logs/filters",
            json={
                "name": "my filter",
                "repo_id": repo.id,
                "search_params": {"invalid_field": "some value"},
                "columns": [],
            },
        )


async def test_log_filter_create_invalid_search_param_custom_field(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_post_bad_request(
            "/users/me/logs/filters",
            json={
                "name": "my filter",
                "repo_id": repo.id,
                "search_params": {"source.INVALID FIELD": "some value"},
                "columns": [],
            },
        )


async def test_log_filter_create_invalid_column_builtin_field(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_post_bad_request(
            "/users/me/logs/filters",
            json={
                "name": "my filter",
                "repo_id": repo.id,
                "search_params": {},
                "columns": [
                    "invalid_field",
                ],
            },
        )


async def test_log_filter_create_invalid_column_custom_field(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_post_bad_request(
            "/users/me/logs/filters",
            json={
                "name": "my filter",
                "repo_id": repo.id,
                "search_params": {},
                "columns": [
                    "source.INVALID FIELD",
                ],
            },
        )


async def test_log_filter_create_invalid_column_duplicated(
    log_read_user_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_user_client.assert_post_bad_request(
        "/users/me/logs/filters",
        json={
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {},
            "columns": [
                "saved_at",
                "saved_at",
            ],
        },
    )


async def test_log_filter_create_invalid_repo(
    log_read_user: PreparedUser, dbm: DatabaseManager
):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_post_bad_request(
            "/users/me/logs/filters",
            json={
                "name": "my filter",
                "repo_id": UNKNOWN_UUID,
                "search_params": {},
                "columns": [],
            },
        )


async def test_log_filter_create_name_already_used(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    data = {
        "name": "my filter",
        "repo_id": repo.id,
        "search_params": {},
        "columns": [],
    }

    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_post_created(
            "/users/me/logs/filters",
            json=data,
        )
        await client.assert_post_constraint_violation(
            "/users/me/logs/filters", json=data
        )


async def test_log_filter_create_as_apikey(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await superadmin_client.assert_post_forbidden(
        "/users/me/logs/filters",
        json={
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {},
            "columns": [],
        },
    )


async def test_log_filter_create_forbidden(
    user_builder: UserBuilder, repo: PreparedRepo
):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper
        await client.assert_post_forbidden(
            "/users/me/logs/filters",
            json={
                "name": "my filter",
                "repo_id": repo.id,
                "search_params": {},
                "columns": [],
            },
        )


async def _test_log_filter_update(
    log_read_user: PreparedUser, data: dict, update: dict, dbm: DatabaseManager
):
    log_filter = await log_read_user.create_log_filter(data)
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_patch_no_content(
            f"/users/me/logs/filters/{log_filter.id}",
            json=update,
        )
    await assert_collection(
        dbm.core_db.log_filters,
        [
            log_filter.expected_document({**update, "user_id": UUID(log_read_user.id)}),
        ],
    )


async def test_log_filter_update_simple(
    log_read_user: PreparedUser, repo: PreparedRepo, dbm: DatabaseManager
):
    await _test_log_filter_update(
        log_read_user,
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {
                "action_type": "some action",
            },
            "columns": [
                "saved_at",
                "action_type",
            ],
        },
        {
            "name": "new name",
        },
        dbm,
    )


async def test_log_filter_update_all_params(
    log_read_user: PreparedUser, repo_builder: RepoBuilder, dbm: DatabaseManager
):
    repo_1 = await repo_builder({})
    repo_2 = await repo_builder({})

    await _test_log_filter_update(
        log_read_user,
        {
            "name": "my filter",
            "repo_id": repo_1.id,
            "search_params": {
                "action_type": "some action",
            },
            "columns": [
                "saved_at",
                "action_type",
            ],
        },
        {
            "name": "new name",
            "repo_id": repo_2.id,
            "search_params": {"action_category": "some category"},
            "columns": [
                "action_type",
                "action_category",
            ],
        },
        dbm,
    )


async def test_log_filter_update_invalid_repo(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    log_filter = await log_read_user.create_log_filter(
        PreparedLogFilter.prepare_data({"repo_id": repo.id})
    )
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_patch_bad_request(
            f"/users/me/logs/filters/{log_filter.id}",
            json={
                "repo_id": UNKNOWN_UUID,
            },
        )


async def test_log_filter_update_name_already_used(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    log_filter_1 = await log_read_user.create_log_filter(
        PreparedLogFilter.prepare_data({"repo_id": repo.id})
    )
    log_filter_2 = await log_read_user.create_log_filter(
        PreparedLogFilter.prepare_data({"repo_id": repo.id})
    )

    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_patch_constraint_violation(
            f"/users/me/logs/filters/{log_filter_1.id}",
            json={"name": log_filter_2.data["name"]},
        )


async def test_log_filter_update_unknown(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_patch_not_found(
            f"/users/me/logs/filters/{UNKNOWN_UUID}", json={}
        )


async def test_log_filter_update_forbidden(
    user_builder: UserBuilder, repo: PreparedRepo
):
    user_1 = await user_builder({"is_superadmin": True})
    user_2 = await user_builder({"is_superadmin": True})

    log_filter = await user_1.create_log_filter(
        PreparedLogFilter.prepare_data({"repo_id": repo.id})
    )

    async with user_2.client() as client:
        client: HttpTestHelper
        await client.assert_patch_not_found(
            f"/users/me/logs/filters/{log_filter.id}",
            json={},
        )


async def test_log_filter_get_simple(log_read_user: PreparedUser, repo: PreparedRepo):
    log_filter = await log_read_user.create_log_filter(
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {},
            "columns": [],
        }
    )
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            f"/users/me/logs/filters/{log_filter.id}",
            expected_json=log_filter.expected_api_response(),
        )


async def test_log_filter_get_all_fields_set(
    log_read_user: PreparedUser, repo: PreparedRepo
):
    log_filter = await log_read_user.create_log_filter(
        {
            "name": "my filter",
            "repo_id": repo.id,
            "search_params": {
                "action_type": "some action",
                "since": "2021-01-01T00:00:00Z",
                "until": "2021-01-02T00:00:00Z",
                "actor.custom_actor_field": "actor field",
                "resource.custom_resource_field": "resource field",
                "source.custom_source_field": "source field",
                "details.custom_details_field": "details field",
            },
            "columns": [
                "saved_at",
                "action",
                "action_type",
                "actor.custom_actor_field",
                "resource.custom_resource_field",
                "source.custom_source_field",
                "details.custom_details_field",
            ],
        }
    )
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            f"/users/me/logs/filters/{log_filter.id}",
            expected_json=log_filter.expected_api_response(),
        )


async def test_log_filter_get_unknown(log_read_user: PreparedUser, repo: PreparedRepo):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_get_not_found(f"/users/me/logs/filters/{UNKNOWN_UUID}")


async def test_log_filter_get_forbidden(user_builder: UserBuilder, repo: PreparedRepo):
    user_1 = await user_builder({"is_superadmin": True})
    user_2 = await user_builder({"is_superadmin": True})

    log_filter = await user_1.create_log_filter(
        PreparedLogFilter.prepare_data({"repo_id": repo.id})
    )

    async with user_2.client() as client:
        client: HttpTestHelper
        await client.assert_get_not_found(f"/users/me/logs/filters/{log_filter.id}")


async def test_log_filter_list(log_read_user: PreparedUser, repo: PreparedRepo):
    log_filters = [
        await log_read_user.create_log_filter(
            {
                "name": f"filter_{i}",
                "repo_id": repo.id,
                "search_params": {
                    "action_type": f"some action {i}",
                },
                "columns": [
                    "saved_at",
                    "action_type",
                ],
            }
        )
        for i in range(5)
    ]

    async with log_read_user.client() as client:
        client: HttpTestHelper
        await do_test_page_pagination_common_scenarios(
            client,
            "/users/me/logs/filters",
            [log_filter.expected_api_response() for log_filter in log_filters],
        )


async def test_log_filter_list_search(log_read_user: PreparedUser, repo: PreparedRepo):
    log_filters = [
        await log_read_user.create_log_filter(
            {
                "name": f"filter_{i}",
                "repo_id": repo.id,
                "search_params": {
                    "action_type": f"some action {i}",
                },
                "columns": [
                    "saved_at",
                    "action_type",
                ],
            }
        )
        for i in range(2)
    ]

    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            "/users/me/logs/filters?q=filter_1",
            expected_json={
                "items": [log_filters[1].expected_api_response()],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 1,
                    "total_pages": 1,
                },
            },
        )


async def test_log_filter_list_empty(log_read_user: PreparedUser):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            "/users/me/logs/filters",
            expected_json={
                "items": [],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 0,
                    "total_pages": 0,
                },
            },
        )


async def test_log_filter_list_segregation(
    user_builder: UserBuilder, repo: PreparedRepo
):
    user_1 = await user_builder({"is_superadmin": True})
    log_filter_1 = await user_1.create_log_filter(
        PreparedLogFilter.prepare_data({"name": "user 1 filter", "repo_id": repo.id})
    )

    user_2 = await user_builder({"is_superadmin": True})
    log_filter_2 = await user_2.create_log_filter(
        PreparedLogFilter.prepare_data({"name": "user 2 filter", "repo_id": repo.id})
    )

    async with user_1.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            "/users/me/logs/filters",
            expected_json={
                "items": [log_filter_1.expected_api_response()],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 1,
                    "total_pages": 1,
                },
            },
        )

    async with user_2.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            "/users/me/logs/filters",
            expected_json={
                "items": [log_filter_2.expected_api_response()],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 1,
                    "total_pages": 1,
                },
            },
        )


async def test_log_filter_list_forbidden(user_builder: UserBuilder):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper
        await client.assert_get_forbidden("/users/me/logs/filters")


async def test_log_filter_delete(
    log_read_user: PreparedUser, repo: PreparedRepo, dbm: DatabaseManager
):
    log_filter = await log_read_user.create_log_filter(
        PreparedLogFilter.prepare_data({"repo_id": repo.id})
    )
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_delete_no_content(f"/users/me/logs/filters/{log_filter.id}")
    await assert_collection(dbm.core_db.log_filters, [])


async def test_log_filter_delete_unknown(log_read_user_client: HttpTestHelper):
    await log_read_user_client.assert_delete_not_found(
        f"/users/me/logs/filters/{UNKNOWN_UUID}"
    )


async def test_log_filter_delete_forbidden(
    user_builder: UserBuilder, repo: PreparedRepo
):
    user_1 = await user_builder({"is_superadmin": True})
    user_2 = await user_builder({"is_superadmin": True})

    log_filter = await user_1.create_log_filter(
        PreparedLogFilter.prepare_data({"repo_id": repo.id})
    )

    async with user_2.client() as client:
        client: HttpTestHelper
        await client.assert_delete_not_found(f"/users/me/logs/filters/{log_filter.id}")
