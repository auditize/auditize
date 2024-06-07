import base64
from datetime import datetime

import callee
import pytest

from auditize.database import DatabaseManager
from auditize.logs.models import Log
from conftest import ApikeyBuilder
from helpers.http import HttpTestHelper
from helpers.logs import UNKNOWN_OBJECT_ID, PreparedLog
from helpers.pagination import (
    do_test_page_pagination_common_scenarios,
    do_test_page_pagination_empty_data,
)
from helpers.repos import PreparedRepo
from helpers.utils import DATETIME_FORMAT

pytestmark = pytest.mark.anyio


async def test_log_repo_access_control(
    apikey_builder: ApikeyBuilder, dbm: DatabaseManager
):
    # Test that access control based on repo_id is properly enforced by the API

    repo_1 = await PreparedRepo.create(dbm)
    repo_2 = await PreparedRepo.create(dbm)

    apikey = await apikey_builder(
        {
            "logs": {
                "repos": [
                    {"repo_id": repo_1.id, "write": True},
                ]
            }
        }
    )

    async with apikey.client() as client:
        await client.assert_post(
            f"/repos/{repo_1.id}/logs",
            json=PreparedLog.prepare_data(),
            expected_status_code=201,
        )
        await client.assert_post(
            f"/repos/{repo_2.id}/logs",
            json=PreparedLog.prepare_data(),
            expected_status_code=403,
        )


async def test_create_log_minimal_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs",
        json=PreparedLog.prepare_data(),
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)},
    )


async def test_create_log_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_post_forbidden(
        f"/repos/{repo.id}/logs", json=PreparedLog.prepare_data()
    )


async def test_create_log_all_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    data = PreparedLog.prepare_data(
        {
            "source": [
                {"name": "ip", "value": "1.1.1.1"},
                {"name": "user_agent", "value": "Mozilla/5.0"},
            ],
            "actor": {
                "type": "user",
                "ref": "user:123",
                "name": "User 123",
                "extra": [{"name": "role", "value": "admin"}],
            },
            "resource": {
                "ref": "core",
                "type": "module",
                "name": "Core Module",
                "extra": [{"name": "creator", "value": "xyz"}],
            },
            "details": [
                {"name": "some_key", "value": "some_value"},
                {"name": "other_key", "value": "other_value"},
            ],
            "tags": [
                {
                    "type": "simple_tag",
                },
                {"ref": "rich_tag:1", "type": "rich_tag", "name": "Rich tag"},
            ],
        }
    )

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)},
    )


@pytest.mark.parametrize("status", ["readonly", "disabled"])
async def test_create_log_not_allowed_by_repo_status(
    superadmin_client: HttpTestHelper, dbm: DatabaseManager, status: str
):
    repo: PreparedRepo = await PreparedRepo.create(
        dbm, PreparedRepo.prepare_data({"status": status})
    )
    await superadmin_client.assert_post_forbidden(
        f"/repos/{repo.id}/logs", json=PreparedLog.prepare_data()
    )


async def test_create_log_missing_action_type(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    data = PreparedLog.prepare_data()
    del data["action"]["type"]
    await log_write_client.assert_post_bad_request(f"/repos/{repo.id}/logs", json=data)


async def test_create_log_invalid_rich_tag(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    invalid_tags = (
        {"ref": "some_tag", "type": "rich_tag"},
        {"ref": "some_other_tag", "name": "Rich tag"},
    )

    for invalid_tag in invalid_tags:
        await log_write_client.assert_post_bad_request(
            f"/repos/{repo.id}/logs",
            json=PreparedLog.prepare_data({"tags": [invalid_tag]}),
        )


async def test_create_log_invalid_identifiers(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    async def test_invalid_identifier(extra):
        await log_write_client.assert_post_bad_request(
            f"/repos/{repo.id}/logs",
            json=PreparedLog.prepare_data(extra),
            expected_json={
                "message": "Invalid request",
                "validation_errors": [
                    {
                        "field": callee.IsA(str),
                        "message": callee.StartsWith("String should match pattern"),
                    }
                ],
            },
        )

    for invalid_identifier in "foo.bar", "foo[bar]", "foo:bar", "foo bar", "FOOBAR":
        # Action
        await test_invalid_identifier(
            {"action": {"category": "valid_category", "type": invalid_identifier}}
        )
        await test_invalid_identifier(
            {"action": {"category": invalid_identifier, "type": "valid_type"}}
        )

        # Actor
        await test_invalid_identifier(
            {
                "actor": {
                    "type": invalid_identifier,
                    "ref": "user:123",
                    "name": "User 123",
                }
            }
        )

        # Resource
        await test_invalid_identifier(
            {
                "resource": {
                    "ref": "core",
                    "type": invalid_identifier,
                    "name": "Core Module",
                }
            }
        )

        # Tag
        await test_invalid_identifier({"tags": [{"type": invalid_identifier}]})

        # Custom fields
        invalid_custom_field = {"name": invalid_identifier, "value": "some_value"}
        await test_invalid_identifier({"details": [invalid_custom_field]})
        await test_invalid_identifier({"source": [invalid_custom_field]})
        await test_invalid_identifier(
            {
                "actor": {
                    "ref": "user:123",
                    "type": "user",
                    "name": "User 123",
                    "extra": [invalid_custom_field],
                }
            }
        )
        await test_invalid_identifier(
            {
                "resource": {
                    "ref": "core",
                    "type": "module",
                    "name": "Core Module",
                    "extra": [invalid_custom_field],
                }
            }
        )


async def test_add_attachment_binary_and_all_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_write_client)

    # some random data generated with /dev/urandom:
    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.bin", data)},
        data={
            "type": "binary",
            "name": "test_file.bin",
            "description": "A binary file",
            "mime_type": "application/octet-stream",
        },
        expected_status_code=204,
    )
    await log.assert_db(
        {
            "attachments": [
                {
                    "name": "test_file.bin",
                    "description": "A binary file",
                    "type": "binary",
                    "mime_type": "application/octet-stream",
                    "data": data,
                    "saved_at": callee.IsA(datetime),
                }
            ]
        }
    )


async def test_add_attachment_too_large(
    log_rw_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_rw_client)
    await log_rw_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("test.txt", "A" * 2048)},
        data={"type": "text"},
        expected_status_code=413,
    )


async def test_add_attachment_invalid_type(
    log_rw_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_rw_client)
    await log_rw_client.assert_post_bad_request(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "invalid type"},
    )


async def test_add_attachment_unknown_log(
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await log_write_client.assert_post_not_found(
        f"/repos/{repo.id}/logs/{UNKNOWN_OBJECT_ID}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
    )


async def test_add_attachment_forbidden(
    log_write_client: HttpTestHelper,
    no_permission_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)
    await no_permission_client.assert_post_forbidden(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
    )


@pytest.mark.parametrize("status", ["readonly", "disabled"])
async def test_add_attachment_not_allowed_by_repo_status(
    superadmin_client: HttpTestHelper, repo: PreparedRepo, status: str
):
    log = await repo.create_log(superadmin_client)
    await repo.update_status(superadmin_client, status)
    await superadmin_client.assert_post_forbidden(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
    )


async def test_get_log_minimal_fields(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}", expected_json=log.expected_api_response()
    )


async def test_get_log_all_fields(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    data = PreparedLog.prepare_data(
        {
            "source": [
                {"name": "ip", "value": "1.1.1.1"},
                {"name": "user_agent", "value": "Mozilla/5.0"},
            ],
            "actor": {
                "type": "user",
                "ref": "user:123",
                "name": "User 123",
                "extra": [{"name": "role", "value": "admin"}],
            },
            "resource": {
                "ref": "core",
                "type": "module",
                "name": "Core Module",
                "extra": [{"name": "creator", "value": "xyz"}],
            },
            "details": [
                {"name": "some_key", "value": "some_value"},
                {"name": "other_key", "value": "other_value"},
            ],
            "tags": [
                {
                    "type": "simple_tag",
                },
                {"ref": "rich_tag:1", "type": "rich_tag", "name": "Rich tag"},
            ],
        }
    )
    log = await repo.create_log(log_write_client, data)
    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
        expected_status_code=204,
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}",
        expected_json=log.expected_api_response(
            {
                "attachments": [
                    {
                        "name": "test.txt",
                        "description": None,
                        "type": "text",
                        "mime_type": "text/plain",
                        "saved_at": DATETIME_FORMAT,
                    }
                ]
            }
        ),
    )


async def test_get_log_not_found(log_read_client: HttpTestHelper, repo: PreparedRepo):
    await log_read_client.assert_get_not_found(
        f"/repos/{repo.id}/logs/{UNKNOWN_OBJECT_ID}"
    )


async def test_get_log_unknown_repo(log_read_client: HttpTestHelper):
    await log_read_client.assert_get_not_found(
        f"/repos/{UNKNOWN_OBJECT_ID}/logs/{UNKNOWN_OBJECT_ID}"
    )


async def test_get_log_forbidden(
    log_write_client: HttpTestHelper,
    no_permission_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}/logs/{log.id}")


@pytest.mark.parametrize(
    "repo_status,status_code", [("readonly", 200), ("disabled", 403)]
)
async def test_get_log_not_enabled_repo_status(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    repo_status: str,
    status_code: int,
):
    log = await repo.create_log(superadmin_client)
    await repo.update_status(superadmin_client, repo_status)
    await superadmin_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}", expected_status_code=status_code
    )


async def test_get_log_attachment_text_and_minimal_fields(
    log_read_client: HttpTestHelper, log_write_client, repo: PreparedRepo
):
    log = await repo.create_log(log_write_client)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.txt", "test data")},
        data={"type": "text_file"},
        expected_status_code=204,
    )

    resp = await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )
    assert resp.headers["Content-Disposition"] == "attachment; filename=file.txt"
    assert resp.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert resp.content == b"test data"


async def test_get_log_attachment_binary_and_all_fields(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)

    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.bin", data)},
        data={"type": "binary", "name": "test_file.bin", "mime_type": "image/jpeg"},
        expected_status_code=204,
    )

    resp = await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )
    assert resp.headers["Content-Disposition"] == "attachment; filename=test_file.bin"
    assert resp.headers["Content-Type"] == "image/jpeg"
    assert resp.content == data


async def test_get_log_attachment_not_found_log_id(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get_not_found(
        f"/repos/{repo.id}/logs/{UNKNOWN_OBJECT_ID}/attachments/0"
    )


async def test_get_log_attachment_not_found_attachment_idx(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log_rw_client.assert_get_not_found(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )


async def test_get_log_attachment_forbidden(
    log_write_client: HttpTestHelper,
    no_permission_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.txt", "test data")},
        data={"type": "text_file"},
        expected_status_code=204,
    )

    await no_permission_client.assert_get_forbidden(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )


@pytest.mark.parametrize(
    "repo_status,status_code", [("readonly", 200), ("disabled", 403)]
)
async def test_get_log_attachment_not_enabled_repo_status(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    repo_status: str,
    status_code: int,
):
    log = await repo.create_log(superadmin_client)
    await log.upload_attachment(superadmin_client)
    await repo.update_status(superadmin_client, repo_status)
    await superadmin_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0",
        expected_status_code=status_code,
    )


async def test_get_logs(
    log_write_client: HttpTestHelper,
    log_read_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log1 = await repo.create_log(log_write_client)
    log2 = await repo.create_log(log_write_client)

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs",
        expected_json={
            "items": [log2.expected_api_response(), log1.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_with_attachment(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log_rw_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.txt", "test data")},
        data={"type": "text_file", "description": "A text file"},
        expected_status_code=204,
    )

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        expected_json={
            "items": [
                log.expected_api_response(
                    {
                        "attachments": [
                            {
                                "name": "file.txt",
                                "description": "A text file",
                                "type": "text_file",
                                "mime_type": "text/plain",
                                "saved_at": DATETIME_FORMAT,
                            }
                        ]
                    }
                )
            ],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_unknown_repo(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get_not_found(f"/repos/{UNKNOWN_OBJECT_ID}/logs")


async def test_get_logs_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}/logs")


async def test_get_logs_limit(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    await repo.create_log(log_rw_client)
    log2 = await repo.create_log(log_rw_client)

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs?limit=1",
        expected_json={
            "items": [log2.expected_api_response()],
            "pagination": {"next_cursor": callee.IsA(str)},
        },
    )


async def test_get_logs_limit_and_cursor(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    logs = [await repo.create_log(log_rw_client) for _ in range(10)]

    # first step, get 5 logs and check the next_cursor
    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs?limit=5",
        expected_json={
            "items": [log.expected_api_response() for log in reversed(logs[-5:])],
            "pagination": {"next_cursor": callee.IsA(str)},
        },
    )
    next_cursor = resp.json()["pagination"]["next_cursor"]

    # second step, get the next 5 logs using the next_cursor from the previous response and check next_cursor is None
    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs?limit=5&cursor={next_cursor}",
        expected_json={
            "items": [log.expected_api_response() for log in reversed(logs[:5])],
            "pagination": {"next_cursor": None},
        },
    )


async def _test_get_logs_filter(
    client: HttpTestHelper,
    repo: PreparedRepo,
    to_be_found,
    search_params,
    *,
    not_to_be_found=None,
):
    # Create logs that are not supposed to be returned
    if not not_to_be_found:
        not_to_be_found = [PreparedLog.prepare_data()]
    for other in not_to_be_found:
        await repo.create_log(client, other)

    # to_be_found is a PreparedLog instance of an already created log
    if isinstance(to_be_found, PreparedLog):
        log = to_be_found
    else:
        # to_be_found is a function that will modify a log data template
        if callable(to_be_found):
            log_data = PreparedLog.prepare_data()
            to_be_found(log_data)
        # to be found is the actual log data
        else:
            log_data = to_be_found
        log = await repo.create_log(client, log_data)

    await client.assert_get(
        f"/repos/{repo.id}/logs",
        params=search_params,
        expected_json={
            "items": [log.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_action_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["action"]["type"] = "find_me"

    await _test_get_logs_filter(log_rw_client, repo, func, {"action_type": "find_me"})


async def test_get_logs_filter_action_category(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["action"]["category"] = "find_me"

    await _test_get_logs_filter(
        log_rw_client, repo, func, {"action_category": "find_me"}
    )


async def test_get_logs_filter_actor_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["actor"] = {"type": "find_me", "ref": "user:123", "name": "User 123"}

    await _test_get_logs_filter(log_rw_client, repo, func, {"actor_type": "find_me"})


async def test_get_logs_filter_actor_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["actor"] = {"type": "user", "ref": "user:123", "name": "find_me"}

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"actor_name": "FIND"})


async def test_get_logs_filter_actor_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["actor"] = {"type": "user", "ref": "user:123", "name": "find_me"}

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"actor_ref": "user:123"})


async def test_get_logs_filter_actor_extra(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    await _test_get_logs_filter(
        log_rw_client,
        repo,
        to_be_found=PreparedLog.prepare_data(
            {
                "actor": {
                    "type": "user",
                    "ref": "user:123",
                    "name": "User 123",
                    "extra": [
                        {"name": "field_1", "value": "foo"},
                        {"name": "field_2", "value": "bar"},
                    ],
                }
            }
        ),
        not_to_be_found=[
            PreparedLog.prepare_data(
                {
                    "actor": {
                        "type": "user",
                        "ref": "user:123",
                        "name": "User 123",
                        "extra": [
                            {"name": "field_1", "value": "bar"},
                            {"name": "field_2", "value": "foo"},
                        ],
                    }
                }
            ),
        ],
        search_params={
            "actor[field_1]": "foo",
            "actor[field_2]": "bar",
        },
    )


async def test_get_logs_filter_resource_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["resource"] = {"ref": "core", "type": "find_me", "name": "Core Module"}

    await _test_get_logs_filter(log_rw_client, repo, func, {"resource_type": "find_me"})


async def test_get_logs_filter_resource_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["resource"] = {"ref": "core", "type": "module", "name": "find_me"}

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"resource_name": "FIND"})


async def test_get_logs_filter_resource_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["resource"] = {"ref": "core", "type": "module", "name": "find_me"}

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"resource_ref": "core"})


async def test_get_logs_filter_resource_extra(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    await _test_get_logs_filter(
        log_rw_client,
        repo,
        to_be_found=PreparedLog.prepare_data(
            {
                "resource": {
                    "type": "config-profile",
                    "ref": "config-profile:123",
                    "name": "Config Profile 123",
                    "extra": [
                        {"name": "field_1", "value": "foo"},
                        {"name": "field_2", "value": "bar"},
                    ],
                }
            }
        ),
        not_to_be_found=[
            PreparedLog.prepare_data(
                {
                    "resource": {
                        "type": "config-profile",
                        "ref": "config-profile:123",
                        "name": "Config Profile 123",
                        "extra": [
                            {"name": "field_1", "value": "bar"},
                            {"name": "field_2", "value": "foo"},
                        ],
                    }
                }
            ),
        ],
        search_params={
            "resource[field_1]": "foo",
            "resource[field_2]": "bar",
        },
    )


async def test_get_logs_filter_details(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    await _test_get_logs_filter(
        log_rw_client,
        repo,
        to_be_found=PreparedLog.prepare_data(
            {
                "details": [
                    {"name": "field_1", "value": "foo"},
                    {"name": "field_2", "value": "bar"},
                ]
            }
        ),
        not_to_be_found=[
            PreparedLog.prepare_data(
                {
                    "details": [
                        {"name": "field_1", "value": "bar"},
                        {"name": "field_2", "value": "foo"},
                    ]
                }
            ),
        ],
        search_params={
            "details[field_1]": "foo",
            "details[field_2]": "bar",
        },
    )


async def test_get_logs_filter_source(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    await _test_get_logs_filter(
        log_rw_client,
        repo,
        to_be_found=PreparedLog.prepare_data(
            {
                "source": [
                    {"name": "field_1", "value": "foo"},
                    {"name": "field_2", "value": "bar"},
                ]
            }
        ),
        not_to_be_found=[
            PreparedLog.prepare_data(
                {
                    "source": [
                        {"name": "field_1", "value": "bar"},
                        {"name": "field_2", "value": "foo"},
                    ]
                }
            ),
        ],
        search_params={
            "source[field_1]": "foo",
            "source[field_2]": "bar",
        },
    )


async def test_get_logs_filter_tag_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["tags"] = [
            {"type": "simple_tag"},
            {"ref": "rich_tag:1", "type": "find_me", "name": "Rich tag"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"tag_type": "find_me"})


async def test_get_logs_filter_tag_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["tags"] = [
            {"type": "simple_tag"},
            {"ref": "rich_tag:1", "type": "rich_tag", "name": "find_me"},
        ]

    # filter on tag_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"tag_name": "FIND"})


async def test_get_logs_filter_tag_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["tags"] = [
            {"type": "simple_tag"},
            {"ref": "find_me", "type": "rich_tag", "name": "Rich tag"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"tag_ref": "find_me"})


async def test_get_logs_filter_attachment_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(
        log_rw_client,
        data=b"test data",
        name="find_me",
        description="A test attachment",
        type="text",
        mime_type="text/plain",
    )
    await _test_get_logs_filter(log_rw_client, repo, log, {"attachment_name": "FIND"})


async def test_get_logs_filter_attachment_description(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(
        log_rw_client,
        data=b"test data",
        name="attachment",
        description="find_me",
        type="text",
        mime_type="text/plain",
    )
    await _test_get_logs_filter(
        log_rw_client, repo, log, {"attachment_description": "FIND"}
    )


async def test_get_logs_filter_attachment_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(
        log_rw_client,
        data=b"test data",
        name="attachment",
        type="find_me",
        mime_type="text/plain",
    )
    await _test_get_logs_filter(
        log_rw_client, repo, log, {"attachment_type": "find_me"}
    )


async def test_get_logs_filter_attachment_mime_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(
        log_rw_client,
        data=b"test data",
        name="attachment",
        type="text",
        mime_type="text/plain",
    )
    await _test_get_logs_filter(
        log_rw_client, repo, log, {"attachment_mime_type": "text/plain"}
    )


async def test_get_logs_filter_node_id_exact_node(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["node_path"] = [
            {"ref": "find_me:1", "name": "Customer 1"},
            {"ref": "find_me:2", "name": "Customer 2"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"node_ref": "find_me:2"})


async def test_get_logs_filter_node_id_ascendant_node(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["node_path"] = [
            {"ref": "find_me:1", "name": "Customer 1"},
            {"ref": "find_me:2", "name": "Customer 2"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"node_ref": "find_me:1"})


async def test_get_logs_filter_since(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"since": "2024-01-01T12:00:00Z"},
        expected_json={
            "items": [log2.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_until(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"until": "2024-01-01T12:00:00Z"},
        expected_json={
            "items": [log1.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_until_milliseconds(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2023-12-31T23:59:59.500Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"until": "2023-12-31T23:59:59Z"},
        expected_json={
            "items": [log1.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_between_since_and_until(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )
    log3 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-03T00:00:00Z")
    )

    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"since": "2024-01-01T12:00:00Z", "until": "2024-01-02T12:00:00Z"},
    )
    assert resp.json() == {
        "items": [log2.expected_api_response()],
        "pagination": {"next_cursor": None},
    }


async def test_get_logs_filter_multiple_criteria(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log1_data = PreparedLog.prepare_data()
    log1_data["action"]["type"] = "find_me_action_type"
    log1 = await repo.create_log(log_rw_client, log1_data)

    log2_data = PreparedLog.prepare_data()
    log2_data["action"]["category"] = "find_me_action_category"
    log2 = await repo.create_log(log_rw_client, log2_data)

    log3_data = PreparedLog.prepare_data()
    log3_data["action"] = {
        "type": "find_me_action_type",
        "category": "find_me_action_category",
    }
    log3 = await repo.create_log(log_rw_client, log3_data)

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={
            "action_type": "find_me_action_type",
            "action_category": "find_me_action_category",
        },
        expected_json={
            "items": [log3.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_empty_string_filter_params(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)

    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={
            "action_type": "",
            "action_category": "",
            "actor_type": "",
            "actor_name": "",
            "resource_type": "",
            "resource_name": "",
            "tag_ref": "",
            "tag_type": "",
            "tag_name": "",
            "node_id": "",
            "since": "",
            "until": "",
        },
    )
    assert resp.json() == {
        "items": [log.expected_api_response()],
        "pagination": {"next_cursor": None},
    }


async def test_get_logs_filter_no_result(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"action_type": "not to be found"},
        expected_json={"items": [], "pagination": {"next_cursor": None}},
    )


class _ConsolidatedDataTest:
    @property
    def relative_path(self) -> str:
        raise NotImplementedError()

    def get_path(self, repo_id: str) -> str:
        return f"/repos/{repo_id}/logs/{self.relative_path}"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        raise NotImplementedError()

    async def test_nominal(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        values = list(reversed(range(5)))  # insert in reverse order to test sorting
        items = await self.create_consolidated_data(superadmin_client, repo, values)
        await do_test_page_pagination_common_scenarios(
            log_read_client,
            self.get_path(repo.id),
            [{"name": item} for item in reversed(items)],
        )

    async def test_empty(self, log_read_client: HttpTestHelper, repo: PreparedRepo):
        await do_test_page_pagination_empty_data(
            log_read_client, self.get_path(repo.id)
        )

    async def test_not_found(self, log_read_client: HttpTestHelper):
        await log_read_client.assert_get_not_found(self.get_path(UNKNOWN_OBJECT_ID))

    async def test_forbidden(
        self, no_permission_client: HttpTestHelper, repo: PreparedRepo
    ):
        await no_permission_client.assert_get_forbidden(self.get_path(repo.id))


class TestLogActionCategories(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "actions/categories"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {"action": {"category": f"category_{val}", "type": f"type_{val}"}}
                ),
            )
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "action": {
                            "category": f"category_{val}",
                            "type": f"type_{val + 10}",
                        }
                    }
                ),
            )

        return [f"category_{val}" for val in values]


class TestLogActionTypes(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "actions/types"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {"action": {"category": f"category_{val}", "type": f"type_{val}"}}
                ),
            )
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "action": {
                            "category": f"category_{val + 10}",
                            "type": f"type_{val}",
                        }
                    }
                ),
            )

        return [f"type_{val}" for val in values]

    async def test_param_category(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        await self.create_consolidated_data(
            superadmin_client, repo, list(reversed(range(5)))
        )

        # test category parameter
        await log_read_client.assert_get(
            f"/repos/{repo.id}/logs/actions/types?category=category_2",
            expected_json={
                "items": [{"name": f"type_{2}"}],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 1,
                    "total_pages": 1,
                },
            },
        )


class TestLogActorTypes(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "actors/types"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "actor": {
                            "type": f"type_{val}",
                            "ref": f"id_{val}",
                            "name": f"name_{val}",
                        }
                    }
                ),
            )
        return [f"type_{val}" for val in values]


class TestLogActorExtras(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "actors/extras"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "actor": {
                            "type": f"type_{val}",
                            "ref": f"id_{val}",
                            "name": f"name_{val}",
                            "extra": [
                                {
                                    "name": f"field_{val}",
                                    "value": f"value",
                                }
                            ],
                        }
                    }
                ),
            )
        return [f"field_{val}" for val in values]


class TestLogResourceTypes(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "resources/types"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "resource": {
                            "ref": f"ref_{val}",
                            "type": f"type_{val}",
                            "name": f"name_{val}",
                        }
                    }
                ),
            )
        return [f"type_{val}" for val in values]


class TestLogResourceExtras(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "resources/extras"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "resource": {
                            "ref": f"ref_{val}",
                            "type": f"type_{val}",
                            "name": f"name_{val}",
                            "extra": [
                                {
                                    "name": f"field_{val}",
                                    "value": f"value",
                                }
                            ],
                        }
                    }
                ),
            )
        return [f"field_{val}" for val in values]


class TestLogTagTypes(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "tags/types"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values[:-1]:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "tags": [
                            {
                                "ref": f"tag_{val}",
                                "type": f"type_{val}",
                                "name": f"name_{val}",
                            }
                        ]
                    }
                ),
            )

        await repo.create_log(
            client,
            PreparedLog.prepare_data({"tags": [{"type": "simple_tag"}]}),
        )

        return [f"type_{val}" for val in values[:-1]] + ["simple_tag"]


class TestLogSourceFields(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "sources"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[str]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "source": [
                            {
                                "name": f"field_{val}",
                                "value": f"value_{val}",
                            }
                        ]
                    }
                ),
            )

        return [f"field_{val}" for val in values]


class TestLogDetailFields(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "details"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "details": [
                            {
                                "name": f"field_{val}",
                                "value": f"value_{val}",
                            }
                        ]
                    }
                ),
            )

        return [f"field_{val}" for val in values]


class TestLogAttachmentTypes(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "attachments/types"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            log = await repo.create_log(client)
            await log.upload_attachment(client, type=f"type_{val}")
        return [f"type_{val}" for val in values]


class TestLogAttachmentMimeTypes(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "attachments/mime-types"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            log = await repo.create_log(client)
            await log.upload_attachment(client, mime_type=f"text/plain{val}")
        return [f"text/plain{val}" for val in values]


@pytest.mark.parametrize(
    "path",
    [
        "/logs",
        "/logs/actions/categories",
        "/logs/actions/types",
        "/logs/actors/types",
        "/logs/actors/extras",
        "/logs/resources/types",
        "/logs/resources/extras",
        "/logs/tags/types",
        "/logs/sources",
        "/logs/details",
        "/logs/attachments/types",
        "/logs/attachments/mime-types",
        "/logs/nodes",
    ],
)
@pytest.mark.parametrize(
    "repo_status,status_code",
    [
        ("readonly", 200),
        ("disabled", 403),
    ],
)
async def test_get_log_related_endpoints_not_enabled_repo_status(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    path: str,
    repo_status: str,
    status_code: int,
):
    await repo.update_status(superadmin_client, repo_status)
    await superadmin_client.assert_get(
        f"/repos/{repo.id}{path}", expected_status_code=status_code
    )


async def test_get_log_nodes_without_filters(
    log_read_client: HttpTestHelper,
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
):
    for i in range(4):
        await repo.create_log(
            superadmin_client,
            PreparedLog.prepare_data(
                {
                    "node_path": [
                        {"ref": f"customer", "name": f"Customer"},
                        {"ref": f"entity:{i}", "name": f"Entity {i}"},
                    ]
                }
            ),
        )

    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/nodes",
        [
            {
                "ref": "customer",
                "name": "Customer",
                "parent_node_ref": None,
                "has_children": True,
            }
        ]
        + [
            {
                "ref": f"entity:{i}",
                "name": f"Entity {i}",
                "parent_node_ref": "customer",
                "has_children": False,
            }
            for i in range(4)
        ],
    )


async def test_get_log_nodes_with_filters(
    log_read_client: HttpTestHelper,
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
):
    for i in range(5):
        for j in "a", "b", "c", "d", "e":
            await repo.create_log(
                superadmin_client,
                PreparedLog.prepare_data(
                    {
                        "node_path": [
                            {"ref": f"customer:{i}", "name": f"Customer {i}"},
                            {"ref": f"entity:{i}-{j}", "name": f"Entity {j}"},
                        ]
                    }
                ),
            )

    # test top-level nodes
    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/nodes?root=true",
        [
            {
                "ref": f"customer:{i}",
                "name": f"Customer {i}",
                "parent_node_ref": None,
                "has_children": True,
            }
            for i in range(5)
        ],
    )

    # test non-top-level nodes
    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/nodes?parent_node_ref=customer:2",
        [
            {
                "ref": f"entity:2-{j}",
                "name": f"Entity {j}",
                "parent_node_ref": "customer:2",
                "has_children": False,
            }
            for j in ("a", "b", "c", "d", "e")
        ],
    )


async def test_get_log_nodes_empty(log_read_client: HttpTestHelper, repo: PreparedRepo):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/nodes"
    )


async def test_get_log_nodes_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}/logs/nodes")


async def test_get_log_node(
    log_read_client: HttpTestHelper,
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await repo.create_log(
        superadmin_client,
        PreparedLog.prepare_data(
            {
                "node_path": [
                    {"ref": "customer", "name": "Customer"},
                    {"ref": "entity", "name": "Entity"},
                ]
            }
        ),
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/nodes/ref:customer",
        expected_json={
            "ref": "customer",
            "name": "Customer",
            "parent_node_ref": None,
            "has_children": True,
        },
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/nodes/ref:entity",
        expected_json={
            "ref": "entity",
            "name": "Entity",
            "parent_node_ref": "customer",
            "has_children": False,
        },
    )


async def test_get_log_node_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(
        f"/repos/{repo.id}/logs/nodes/ref:some_value"
    )


@pytest.mark.parametrize(
    "repo_status,status_code", [("readonly", 200), ("disabled", 403)]
)
async def test_get_log_node_not_enabled_repo_status(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    repo_status: str,
    status_code: int,
):
    await repo.create_log(
        superadmin_client,
        PreparedLog.prepare_data(
            {
                "node_path": [
                    {"ref": "customer", "name": "Customer"},
                ],
            }
        ),
    )
    await repo.update_status(superadmin_client, repo_status)
    await superadmin_client.assert_get(
        f"/repos/{repo.id}/logs/nodes/ref:customer", expected_status_code=status_code
    )
