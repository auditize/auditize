import callee
import pytest

from auditize.database import DatabaseManager
from conftest import UserBuilder
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.logfilters import DEFAULT_SEARCH_PARAMETERS, PreparedLogFilter
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.repos import PreparedRepo
from helpers.users import PreparedUser

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
        [log_filter.expected_document({"user_id": user.id})],
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
    params = {k: "some value" for k in DEFAULT_SEARCH_PARAMETERS}
    params["since"] = "2021-01-01T00:00:00Z"
    params["until"] = "2021-01-02T00:00:00Z"
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
                "attachment_description",
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


async def test_log_filter_create_invalid_repo(
    log_read_user: PreparedUser, dbm: DatabaseManager
):
    async with log_read_user.client() as client:
        client: HttpTestHelper
        await client.assert_post_bad_request(
            "/users/me/logs/filters",
            json={
                "name": "my filter",
                "repo_id": UNKNOWN_OBJECT_ID,
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
