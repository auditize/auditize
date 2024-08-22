import base64
from datetime import datetime
from unittest.mock import patch

import callee
import pytest

from auditize.database import DatabaseManager
from conftest import ApikeyBuilder, RepoBuilder, UserBuilder
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.log import UNKNOWN_UUID, PreparedLog
from helpers.pagination import (
    do_test_page_pagination_common_scenarios,
    do_test_page_pagination_empty_data,
)
from helpers.repo import PreparedRepo
from helpers.utils import DATETIME_FORMAT

pytestmark = pytest.mark.anyio


async def test_log_repo_access_control(
    apikey_builder: ApikeyBuilder, repo_builder: RepoBuilder
):
    # Test that access control based on repo_id is properly enforced by the API

    repo_1 = await repo_builder({})
    repo_2 = await repo_builder({})

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
                {"name": "user-agent", "value": "Mozilla/5.0"},
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
                {"name": "some-key", "value": "some_value"},
                {"name": "other-key", "value": "other_value"},
            ],
            "tags": [
                {
                    "type": "simple-tag",
                },
                {"ref": "rich_tag:1", "type": "rich-tag", "name": "Rich tag"},
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
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder, status: str
):
    repo = await repo_builder({"status": status})
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
                "localized_message": None,
                "validation_errors": [
                    {
                        "field": callee.IsA(str),
                        "message": callee.StartsWith("String should match pattern"),
                    }
                ],
            },
        )

    for invalid_identifier in (
        "foo.bar",
        "foo[bar]",
        "foo:bar",
        "foo bar",
        "FOOBAR",
        "foo_bar",
    ):
        # Action
        await test_invalid_identifier(
            {"action": {"category": "valid-category", "type": invalid_identifier}}
        )
        await test_invalid_identifier(
            {"action": {"category": invalid_identifier, "type": "valid-type"}}
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


async def test_create_log_cannot_have_entities_with_same_name_and_parent(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    """Check that we cannot create a log with the same entity name (but different refs) twice at the same level"""

    await repo.create_log_with(
        log_write_client,
        {
            "entity_path": [
                {"ref": "Entity A", "name": "Entity A"},
                {"ref": "Entity B", "name": "Entity B"},
            ]
        },
    )

    await log_write_client.assert_post_constraint_violation(
        f"/repos/{repo.id}/logs",
        json=PreparedLog.prepare_data(
            {
                "entity_path": [
                    {"ref": "Entity A", "name": "Entity A"},
                    {"ref": "Another ref for Entity B", "name": "Entity B"},
                ]
            }
        ),
    )


async def test_create_log_can_have_have_entities_with_same_name_but_different_parents(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    """Check that we can create a log with the same entity name as long as they have different parents"""

    await repo.create_log_with(
        log_write_client,
        {
            "entity_path": [
                {"ref": "Entity A", "name": "Entity A"},
                {"ref": "Entity B ref 1", "name": "Entity B"},
            ]
        },
    )

    await log_write_client.assert_post_created(
        f"/repos/{repo.id}/logs",
        json=PreparedLog.prepare_data(
            {
                "entity_path": [
                    {"ref": "Entity C", "name": "Entity C"},
                    {"ref": "Entity B ref 2", "name": "Entity B"},
                ]
            }
        ),
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
            "mime_type": "application/octet-stream",
        },
        expected_status_code=204,
    )
    await log.assert_db(
        {
            "attachments": [
                {
                    "name": "test_file.bin",
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
        f"/repos/{repo.id}/logs/{UNKNOWN_UUID}/attachments",
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
                {"name": "user-agent", "value": "Mozilla/5.0"},
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
                {"name": "some-key", "value": "some_value"},
                {"name": "other-key", "value": "other_value"},
            ],
            "tags": [
                {
                    "type": "simple-tag",
                },
                {"ref": "rich_tag:1", "type": "rich-tag", "name": "Rich tag"},
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
                        "type": "text",
                        "mime_type": "text/plain",
                        "saved_at": DATETIME_FORMAT,
                    }
                ]
            }
        ),
    )


async def test_get_log_not_found(log_read_client: HttpTestHelper, repo: PreparedRepo):
    await log_read_client.assert_get_not_found(f"/repos/{repo.id}/logs/{UNKNOWN_UUID}")


async def test_get_log_unknown_repo(log_read_client: HttpTestHelper):
    await log_read_client.assert_get_not_found(
        f"/repos/{UNKNOWN_UUID}/logs/{UNKNOWN_UUID}"
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
        data={"type": "text-file"},
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
        f"/repos/{repo.id}/logs/{UNKNOWN_UUID}/attachments/0"
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
        data={"type": "text-file"},
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
        data={"type": "text-file"},
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
                                "type": "text-file",
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
    await log_read_client.assert_get_not_found(f"/repos/{UNKNOWN_UUID}/logs")


async def test_get_logs_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}/logs")


# Bug coverage
async def test_get_logs_access_control_without_explicit_entities(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    resp = await superadmin_client.assert_post_ok(
        "/auth/access-token",
        json={"permissions": {"logs": {"repos": [{"repo_id": repo.id, "read": True}]}}},
    )
    access_token = resp.json()["access_token"]

    client = HttpTestHelper.spawn()
    await client.assert_get_ok(
        f"/repos/{repo.id}/logs", headers={"Authorization": f"Bearer {access_token}"}
    )


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
    search_params: dict,
    expected_log: PreparedLog,
    *,
    extra_log=True,
):
    # Create a log that is not supposed to be returned
    if extra_log:
        await repo.create_log(client)

    await client.assert_get(
        f"/repos/{repo.id}/logs",
        params=search_params,
        expected_json={
            "items": [expected_log.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_action_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client, {"action": {"category": "category", "type": "find-me"}}
    )

    await _test_get_logs_filter(log_rw_client, repo, {"action_type": "find-me"}, log)


async def test_get_logs_filter_action_category(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client, {"action": {"category": "find-me", "type": "type"}}
    )

    await _test_get_logs_filter(
        log_rw_client, repo, {"action_category": "find-me"}, log
    )


async def test_get_logs_filter_actor_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"actor": {"type": "find-me", "ref": "user:123", "name": "User 123"}},
    )

    await _test_get_logs_filter(log_rw_client, repo, {"actor_type": "find-me"}, log)


async def test_get_logs_filter_actor_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "user:123", "name": "find_me"}}
    )

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"actor_name": "FIND"}, log)


async def test_get_logs_filter_actor_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "user:123", "name": "find_me"}}
    )

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"actor_ref": "user:123"}, log)


async def test_get_logs_filter_actor_extra(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log_1 = await repo.create_log_with(
        log_rw_client,
        {
            "actor": {
                "type": "user",
                "ref": "user:123",
                "name": "User 123",
                "extra": [
                    {"name": "field-1", "value": "foo"},
                    {"name": "field-2", "value": "bar"},
                ],
            }
        },
    )
    log_2 = await repo.create_log_with(
        log_rw_client,
        {
            "actor": {
                "type": "user",
                "ref": "user:123",
                "name": "User 123",
                "extra": [
                    {"name": "field-1", "value": "bar"},
                    {"name": "field-2", "value": "foo"},
                ],
            }
        },
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {
            "actor.field-1": "foo",
            "actor.field-2": "bar",
        },
        log_1,
        extra_log=False,
    )


async def test_get_logs_filter_resource_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"resource": {"ref": "core", "type": "find-me", "name": "Core Module"}},
    )

    await _test_get_logs_filter(log_rw_client, repo, {"resource_type": "find-me"}, log)


async def test_get_logs_filter_resource_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"resource": {"ref": "core", "type": "module", "name": "find_me"}},
    )

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"resource_name": "FIND"}, log)


async def test_get_logs_filter_resource_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"resource": {"ref": "core", "type": "module", "name": "find_me"}},
    )

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"resource_ref": "core"}, log)


async def test_get_logs_filter_resource_extra(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log_1 = await repo.create_log_with(
        log_rw_client,
        {
            "resource": {
                "type": "config-profile",
                "ref": "config-profile:123",
                "name": "Config Profile 123",
                "extra": [
                    {"name": "field-1", "value": "foo"},
                    {"name": "field-2", "value": "bar"},
                ],
            }
        },
    )
    log_2 = await repo.create_log_with(
        log_rw_client,
        {
            "resource": {
                "type": "config-profile",
                "ref": "config-profile:123",
                "name": "Config Profile 123",
                "extra": [
                    {"name": "field-1", "value": "bar"},
                    {"name": "field-2", "value": "foo"},
                ],
            }
        },
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {
            "resource.field-1": "foo",
            "resource.field-2": "bar",
        },
        log_1,
        extra_log=False,
    )


async def test_get_logs_filter_details(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log_1 = await repo.create_log_with(
        log_rw_client,
        {
            "details": [
                {"name": "field-1", "value": "foo"},
                {"name": "field-2", "value": "bar"},
            ]
        },
    )

    log_2 = await repo.create_log_with(
        log_rw_client,
        {
            "details": [
                {"name": "field-1", "value": "bar"},
                {"name": "field-2", "value": "foo"},
            ]
        },
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {
            "details.field-1": "foo",
            "details.field-2": "bar",
        },
        log_1,
        extra_log=False,
    )


async def test_get_logs_filter_source(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log_1 = await repo.create_log_with(
        log_rw_client,
        {
            "source": [
                {"name": "field-1", "value": "foo"},
                {"name": "field-2", "value": "bar"},
            ]
        },
    )

    log_2 = await repo.create_log_with(
        log_rw_client,
        {
            "source": [
                {"name": "field-1", "value": "bar"},
                {"name": "field-2", "value": "foo"},
            ]
        },
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {
            "source.field-1": "foo",
            "source.field-2": "bar",
        },
        log_1,
        extra_log=False,
    )


async def test_get_logs_filter_tag_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "simple-tag"},
                {"ref": "rich_tag:1", "type": "find-me", "name": "Rich tag"},
            ]
        },
    )

    await _test_get_logs_filter(log_rw_client, repo, {"tag_type": "find-me"}, log)


async def test_get_logs_filter_tag_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "simple-tag"},
                {"ref": "rich_tag:1", "type": "rich-tag", "name": "find_me"},
            ]
        },
    )

    # filter on tag_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"tag_name": "FIND"}, log)


async def test_get_logs_filter_tag_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "simple-tag"},
                {"ref": "find_me", "type": "rich-tag", "name": "Rich tag"},
            ]
        },
    )

    await _test_get_logs_filter(log_rw_client, repo, {"tag_ref": "find_me"}, log)


async def test_get_logs_filter_has_attachment(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log_with_attachment = await repo.create_log(log_rw_client)
    await log_with_attachment.upload_attachment(
        log_rw_client,
        data=b"test data",
        name="find_me",
        type="text",
        mime_type="text/plain",
    )
    log_without_attachment = await repo.create_log(log_rw_client)

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {"has_attachment": True},
        log_with_attachment,
        extra_log=False,
    )
    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {"has_attachment": False},
        log_without_attachment,
        extra_log=False,
    )


async def test_get_logs_filter_attachment_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(
        log_rw_client,
        data=b"test data",
        name="find_me",
        type="text",
        mime_type="text/plain",
    )
    await _test_get_logs_filter(log_rw_client, repo, {"attachment_name": "FIND"}, log)


async def test_get_logs_filter_attachment_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(
        log_rw_client,
        data=b"test data",
        name="attachment",
        type="find-me",
        mime_type="text/plain",
    )
    await _test_get_logs_filter(
        log_rw_client, repo, {"attachment_type": "find-me"}, log
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
        log_rw_client, repo, {"attachment_mime_type": "text/plain"}, log
    )


async def test_get_logs_filter_entity_id_exact_entity(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "entity_path": [
                {"ref": "find_me:1", "name": "Customer 1"},
                {"ref": "find_me:2", "name": "Entity A"},
            ]
        },
    )

    await _test_get_logs_filter(log_rw_client, repo, {"entity_ref": "find_me:2"}, log)


async def test_get_logs_filter_entity_id_ascendant_entity(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "entity_path": [
                {"ref": "find_me:1", "name": "Customer 1"},
                {"ref": "find_me:2", "name": "Entity B"},
            ]
        },
    )

    await _test_get_logs_filter(log_rw_client, repo, {"entity_ref": "find_me:1"}, log)


async def test_get_logs_filter_since(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {"since": "2024-01-01T12:00:00Z"},
        log2,
        extra_log=False,
    )


async def test_get_logs_filter_until(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {"until": "2024-01-01T12:00:00Z"},
        log1,
        extra_log=False,
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

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {"until": "2023-12-31T23:59:59Z"},
        log1,
        extra_log=False,
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

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {"since": "2024-01-01T12:00:00Z", "until": "2024-01-02T12:00:00Z"},
        log2,
        extra_log=False,
    )


async def test_get_logs_filter_multiple_criteria(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log_1 = await repo.create_log_with(
        log_rw_client,
        {
            "action": {"type": "find-me-action-type", "category": "category"},
        },
    )

    log_2 = await repo.create_log_with(
        log_rw_client,
        {
            "action": {"type": "type", "category": "find-me-action-category"},
        },
    )

    log_3 = await repo.create_log_with(
        log_rw_client,
        {
            "action": {
                "type": "find-me-action-type",
                "category": "find-me-action-category",
            },
        },
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {
            "action_type": "find-me-action-type",
            "action_category": "find-me-action-category",
        },
        log_3,
        extra_log=False,
    )


async def test_get_logs_empty_string_filter_params(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {
            "action_type": "",
            "action_category": "",
            "actor_type": "",
            "actor_name": "",
            "resource_type": "",
            "resource_name": "",
            "tag_ref": "",
            "tag_type": "",
            "tag_name": "",
            "entity_id": "",
            "since": "",
            "until": "",
        },
        log,
        extra_log=False,
    )


async def test_get_logs_filter_no_result(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)

    await log_rw_client.assert_get_ok(
        f"/repos/{repo.id}/logs",
        params={"action_type": "not to be found"},
        expected_json={"items": [], "pagination": {"next_cursor": None}},
    )


async def _test_get_logs_visibility(
    builder: ApikeyBuilder | UserBuilder,
    repo: PreparedRepo,
    authorized_entities: list[str],
    search_params: dict[str, str],
    expected_logs: list[PreparedLog],
):
    apikey = await builder(
        {
            "logs": {
                "repos": [
                    {
                        "repo_id": repo.id,
                        "read": True,
                        "readable_entities": authorized_entities,
                    }
                ]
            }
        }
    )

    async with apikey.client() as client:
        await client.assert_get_ok(
            f"/repos/{repo.id}/logs",
            params=search_params,
            expected_json={
                "items": [log.expected_api_response() for log in expected_logs],
                "pagination": {"next_cursor": None},
            },
        )


async def test_get_logs_with_limited_entity_visibility_1(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
):
    log1 = await repo.create_log_with_entity_path(superadmin_client, ["A"])
    log2 = await repo.create_log_with_entity_path(superadmin_client, ["B"])

    await _test_get_logs_visibility(apikey_builder, repo, ["A"], {}, [log1])
    await _test_get_logs_visibility(apikey_builder, repo, ["B"], {}, [log2])
    await _test_get_logs_visibility(apikey_builder, repo, [], {}, [log2, log1])


async def test_get_logs_with_limited_entity_visibility_2(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
):
    log1 = await repo.create_log_with_entity_path(superadmin_client, ["A", "B", "C"])
    log2 = await repo.create_log_with_entity_path(superadmin_client, ["A", "B"])
    log3 = await repo.create_log_with_entity_path(superadmin_client, ["A"])

    await _test_get_logs_visibility(apikey_builder, repo, ["A"], {}, [log3, log2, log1])
    await _test_get_logs_visibility(apikey_builder, repo, ["B"], {}, [log2, log1])
    await _test_get_logs_visibility(apikey_builder, repo, ["C"], {}, [log1])


async def test_get_logs_with_limited_entity_visibility_3(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
):
    log1 = await repo.create_log_with_entity_path(superadmin_client, ["A", "B", "C"])
    log2 = await repo.create_log_with_entity_path(superadmin_client, ["A", "D", "E"])

    await _test_get_logs_visibility(apikey_builder, repo, ["B"], {}, [log1])
    await _test_get_logs_visibility(apikey_builder, repo, ["D"], {}, [log2])


async def test_get_logs_with_limited_entity_visibility_4(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    user_builder: UserBuilder,
):
    log1 = await repo.create_log_with_entity_path(superadmin_client, ["A", "B", "C"])
    log2 = await repo.create_log_with_entity_path(superadmin_client, ["A", "B", "D"])

    await _test_get_logs_visibility(user_builder, repo, ["B"], {}, [log2, log1])
    await _test_get_logs_visibility(user_builder, repo, ["D"], {}, [log2])
    await _test_get_logs_visibility(
        user_builder, repo, ["B"], {"entity_ref": "B"}, [log2, log1]
    )
    await _test_get_logs_visibility(
        user_builder, repo, ["B"], {"entity_ref": "C"}, [log1]
    )
    await _test_get_logs_visibility(
        user_builder, repo, ["C"], {"entity_ref": "B"}, [log1]
    )
    await _test_get_logs_visibility(user_builder, repo, ["C"], {"entity_ref": "D"}, [])


async def _test_get_log_visibility(
    builder: ApikeyBuilder | UserBuilder,
    repo: PreparedRepo,
    authorized_entities: list[str],
    log: PreparedLog,
    expected_status_code: int,
):
    apikey = await builder(
        {
            "logs": {
                "repos": [
                    {
                        "repo_id": repo.id,
                        "read": True,
                        "readable_entities": authorized_entities,
                    }
                ]
            }
        }
    )

    async with apikey.client() as client:
        if expected_status_code == 200:
            await client.assert_get_ok(
                f"/repos/{repo.id}/logs/{log.id}",
                expected_json=log.expected_api_response(),
            )
        else:
            await client.assert_get(
                f"/repos/{repo.id}/logs/{log.id}",
                expected_status_code=expected_status_code,
            )


async def test_get_log_visibility(
    superadmin_client: HttpTestHelper, repo: PreparedRepo, apikey_builder: ApikeyBuilder
):
    log1 = await repo.create_log_with_entity_path(superadmin_client, ["A", "B", "C"])
    log2 = await repo.create_log_with_entity_path(superadmin_client, ["A", "B", "D"])

    await _test_get_log_visibility(apikey_builder, repo, ["B"], log1, 200)
    await _test_get_log_visibility(apikey_builder, repo, ["B"], log2, 200)
    await _test_get_log_visibility(apikey_builder, repo, ["C", "D"], log1, 200)
    await _test_get_log_visibility(apikey_builder, repo, ["C", "D"], log2, 200)
    await _test_get_log_visibility(apikey_builder, repo, ["C"], log1, 200)
    await _test_get_log_visibility(apikey_builder, repo, ["C"], log2, 404)


async def _test_get_log_entities_visibility(
    builder: ApikeyBuilder | UserBuilder,
    repo: PreparedRepo,
    authorized_entities: list[str],
    search_params: dict[str, str],
    expected: list[str],
):
    authenticated = await builder(
        {
            "logs": {
                "repos": [
                    {
                        "repo_id": repo.id,
                        "read": True,
                        "readable_entities": authorized_entities,
                    }
                ]
            }
        }
    )

    async with authenticated.client() as client:
        await client.assert_get_ok(
            f"/repos/{repo.id}/logs/entities",
            params=search_params,
            expected_json={
                "items": [
                    {
                        "ref": entity_ref,
                        "name": entity_ref,
                        "parent_entity_ref": callee.OneOf(
                            callee.Eq(None), callee.IsA(str)
                        ),
                        "has_children": callee.IsA(bool),
                    }
                    for entity_ref in expected
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": len(expected),
                    "total_pages": 1 if len(expected) > 0 else 0,
                },
            },
        )


async def test_get_log_entities_visibility(
    superadmin_client: HttpTestHelper, repo: PreparedRepo, apikey_builder: ApikeyBuilder
):
    # Create a tree of entities:
    # A
    # ├── AA
    # │   ├── AAA
    # │   └── AAB
    # └── AB
    #     ├── ABA
    #     └── ABB
    # B
    # ├── BA
    #     ├── BAA
    #     └── BAB
    #
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AA", "AAA"])
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AA", "AAB"])
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AB", "ABA"])
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AB", "ABB"])
    await repo.create_log_with_entity_path(superadmin_client, ["B", "BA", "BAA"])
    await repo.create_log_with_entity_path(superadmin_client, ["B", "BA", "BAB"])

    # Test with a user without entity restriction
    await _test_get_log_entities_visibility(
        apikey_builder, repo, [], {"root": "1"}, ["A", "B"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, [], {"parent_entity_ref": "A"}, ["AA", "AB"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, [], {"parent_entity_ref": "AA"}, ["AAA", "AAB"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, [], {"parent_entity_ref": "AB"}, ["ABA", "ABB"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, [], {"parent_entity_ref": "B"}, ["BA"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, [], {"parent_entity_ref": "BA"}, ["BAA", "BAB"]
    )

    # Test with a user with entity permission on entity "A"
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["A"], {"root": "1"}, ["A"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["A"], {"parent_entity_ref": "A"}, ["AA", "AB"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["A"], {"parent_entity_ref": "AA"}, ["AAA", "AAB"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["A"], {"parent_entity_ref": "AB"}, ["ABA", "ABB"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["A"], {"parent_entity_ref": "B"}, []
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["A"], {"parent_entity_ref": "BA"}, []
    )

    # Test with a user with entity permission on entity "AA"
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AA"], {"root": "1"}, ["A"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AA"], {"parent_entity_ref": "A"}, ["AA"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AA"], {"parent_entity_ref": "AA"}, ["AAA", "AAB"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AA"], {"parent_entity_ref": "AB"}, []
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AA"], {"parent_entity_ref": "B"}, []
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AA"], {"parent_entity_ref": "B"}, []
    )

    # Test with a user with entity permission on entity "AAA"
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AAA"], {"root": "1"}, ["A"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AAA"], {"parent_entity_ref": "A"}, ["AA"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AAA"], {"parent_entity_ref": "AA"}, ["AAA"]
    )
    await _test_get_log_entities_visibility(
        apikey_builder, repo, ["AAA"], {"parent_entity_ref": "B"}, []
    )


async def _test_get_log_entity_visibility(
    builder: ApikeyBuilder | UserBuilder,
    repo: PreparedRepo,
    authorized_entities: list[str],
    entity_ref: str,
    expected_status_code: int,
):
    apikey = await builder(
        {
            "logs": {
                "repos": [
                    {
                        "repo_id": repo.id,
                        "read": True,
                        "readable_entities": authorized_entities,
                    }
                ]
            }
        }
    )

    async with apikey.client() as client:
        if expected_status_code == 200:
            await client.assert_get_ok(
                f"/repos/{repo.id}/logs/entities/ref:{entity_ref}",
                expected_json={
                    "ref": entity_ref,
                    "name": entity_ref,
                    "parent_entity_ref": callee.OneOf(callee.Eq(None), callee.IsA(str)),
                    "has_children": callee.IsA(bool),
                },
            )
        else:
            await client.assert_get(
                f"/repos/{repo.id}/logs/entities/ref:{entity_ref}",
                expected_status_code=expected_status_code,
            )


async def test_get_log_entity_visibility(
    superadmin_client: HttpTestHelper, repo: PreparedRepo, apikey_builder: ApikeyBuilder
):
    # Create a tree of entities:
    # A
    # ├── AA
    # │   ├── AAA
    # │   └── AAB
    # └── AB
    #     ├── ABA
    #     └── ABB

    await repo.create_log_with_entity_path(superadmin_client, ["A", "AA", "AAA"])
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AA", "AAB"])
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AB", "ABA"])
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AB", "ABB"])

    await _test_get_log_entity_visibility(apikey_builder, repo, [], "A", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, [], "AA", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, [], "AAA", 200)

    await _test_get_log_entity_visibility(apikey_builder, repo, ["A"], "A", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["A"], "AA", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["A"], "AAA", 200)

    await _test_get_log_entity_visibility(apikey_builder, repo, ["AA"], "A", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AA"], "AA", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AA"], "AAA", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AA"], "AB", 404)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AA"], "ABA", 404)

    await _test_get_log_entity_visibility(apikey_builder, repo, ["AAA"], "A", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AAA"], "AA", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AAA"], "AAA", 200)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AAA"], "AAB", 404)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AAA"], "AB", 404)
    await _test_get_log_entity_visibility(apikey_builder, repo, ["AAA"], "ABA", 404)


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
        await log_read_client.assert_get_not_found(self.get_path(UNKNOWN_UUID))

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
                    {"action": {"category": f"category-{val}", "type": f"type-{val}"}}
                ),
            )
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "action": {
                            "category": f"category-{val}",
                            "type": f"type-{val + 10}",
                        }
                    }
                ),
            )

        return [f"category-{val}" for val in values]


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
                    {"action": {"category": f"category-{val}", "type": f"type-{val}"}}
                ),
            )
            await repo.create_log(
                client,
                PreparedLog.prepare_data(
                    {
                        "action": {
                            "category": f"category-{val + 10}",
                            "type": f"type-{val}",
                        }
                    }
                ),
            )

        return [f"type-{val}" for val in values]

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
            f"/repos/{repo.id}/logs/actions/types?category=category-2",
            expected_json={
                "items": [{"name": f"type-{2}"}],
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
                            "type": f"type-{val}",
                            "ref": f"id_{val}",
                            "name": f"name_{val}",
                        }
                    }
                ),
            )
        return [f"type-{val}" for val in values]


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
                            "type": f"type-{val}",
                            "ref": f"id_{val}",
                            "name": f"name_{val}",
                            "extra": [
                                {
                                    "name": f"field-{val}",
                                    "value": f"value",
                                }
                            ],
                        }
                    }
                ),
            )
        return [f"field-{val}" for val in values]


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
                            "type": f"type-{val}",
                            "name": f"name_{val}",
                        }
                    }
                ),
            )
        return [f"type-{val}" for val in values]


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
                            "type": f"type-{val}",
                            "name": f"name_{val}",
                            "extra": [
                                {
                                    "name": f"field-{val}",
                                    "value": f"value",
                                }
                            ],
                        }
                    }
                ),
            )
        return [f"field-{val}" for val in values]


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
                                "type": f"type-{val}",
                                "name": f"name_{val}",
                            }
                        ]
                    }
                ),
            )

        await repo.create_log(
            client,
            PreparedLog.prepare_data({"tags": [{"type": "simple-tag"}]}),
        )

        return [f"type-{val}" for val in values[:-1]] + ["simple-tag"]


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
                                "name": f"field-{val}",
                                "value": f"value_{val}",
                            }
                        ]
                    }
                ),
            )

        return [f"field-{val}" for val in values]


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
                                "name": f"field-{val}",
                                "value": f"value_{val}",
                            }
                        ]
                    }
                ),
            )

        return [f"field-{val}" for val in values]


class TestLogAttachmentTypes(_ConsolidatedDataTest):
    @property
    def relative_path(self) -> str:
        return "attachments/types"

    async def create_consolidated_data(
        self, client: HttpTestHelper, repo: PreparedRepo, values: list[int]
    ) -> list[str]:
        for val in values:
            log = await repo.create_log(client)
            await log.upload_attachment(client, type=f"type-{val}")
        return [f"type-{val}" for val in values]


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


async def test_log_entity_consolidation_rename_entity(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log_with(
        superadmin_client,
        {
            "entity_path": [
                {"ref": "A", "name": "Name of A"},
                {"ref": "AA", "name": "Name of AA"},
            ]
        },
    )
    await repo.create_log_with(
        superadmin_client,
        {
            "entity_path": [
                {"ref": "A", "name": "Name of A"},
                {"ref": "AA", "name": "New name of AA"},
            ]
        },
    )
    await assert_collection(
        repo.db.log_entities,
        [
            {
                "_id": callee.Any(),
                "parent_entity_ref": None,
                "ref": "A",
                "name": "Name of A",
            },
            {
                "_id": callee.Any(),
                "parent_entity_ref": "A",
                "ref": "AA",
                "name": "New name of AA",
            },
        ],
    )


async def test_log_entity_consolidation_move_entity(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AA"])
    await repo.create_log_with_entity_path(superadmin_client, ["B"])
    await repo.create_log_with_entity_path(superadmin_client, ["B", "AA"])

    await assert_collection(
        repo.db.log_entities,
        [
            {
                "_id": callee.Any(),
                "parent_entity_ref": None,
                "ref": "A",
                "name": "A",
            },
            {
                "_id": callee.Any(),
                "parent_entity_ref": "B",
                "ref": "AA",
                "name": "AA",
            },
            {
                "_id": callee.Any(),
                "parent_entity_ref": None,
                "ref": "B",
                "name": "B",
            },
        ],
    )


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
        "/logs/entities?root=true",
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


async def test_get_log_entities_with_filters(
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
                        "entity_path": [
                            {"ref": f"customer:{i}", "name": f"Customer {i}"},
                            {"ref": f"entity:{i}-{j}", "name": f"Entity {j}"},
                        ]
                    }
                ),
            )

    # test top-level entities
    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/entities?root=true",
        [
            {
                "ref": f"customer:{i}",
                "name": f"Customer {i}",
                "parent_entity_ref": None,
                "has_children": True,
            }
            for i in range(5)
        ],
    )

    # test non-top-level entities
    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/entities?parent_entity_ref=customer:2",
        [
            {
                "ref": f"entity:2-{j}",
                "name": f"Entity {j}",
                "parent_entity_ref": "customer:2",
                "has_children": False,
            }
            for j in ("a", "b", "c", "d", "e")
        ],
    )


async def test_get_log_entities_empty(log_read_client: HttpTestHelper, repo: PreparedRepo):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/entities?root=true"
    )


async def test_get_log_entities_no_root_or_parent_entity_ref_params(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get_bad_request(f"/repos/{repo.id}/logs/entities")


async def test_get_log_entities_both_root_or_parent_entity_ref_params(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get_bad_request(
        f"/repos/{repo.id}/logs/entities",
        params={"root": "true", "parent_entity_ref": "customer:1"},
    )


async def test_get_log_entities_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}/logs/entities")


async def test_get_log_entity(
    log_read_client: HttpTestHelper,
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await repo.create_log(
        superadmin_client,
        PreparedLog.prepare_data(
            {
                "entity_path": [
                    {"ref": "customer", "name": "Customer"},
                    {"ref": "entity", "name": "Entity"},
                ]
            }
        ),
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/entities/ref:customer",
        expected_json={
            "ref": "customer",
            "name": "Customer",
            "parent_entity_ref": None,
            "has_children": True,
        },
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/entities/ref:entity",
        expected_json={
            "ref": "entity",
            "name": "Entity",
            "parent_entity_ref": "customer",
            "has_children": False,
        },
    )


async def test_get_log_entity_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(
        f"/repos/{repo.id}/logs/entities/ref:some_value"
    )


@pytest.mark.parametrize(
    "repo_status,status_code", [("readonly", 200), ("disabled", 403)]
)
async def test_get_log_entity_not_enabled_repo_status(
    superadmin_client: HttpTestHelper,
    repo: PreparedRepo,
    repo_status: str,
    status_code: int,
):
    await repo.create_log(
        superadmin_client,
        PreparedLog.prepare_data(
            {
                "entity_path": [
                    {"ref": "customer", "name": "Customer"},
                ],
            }
        ),
    )
    await repo.update_status(superadmin_client, repo_status)
    await superadmin_client.assert_get(
        f"/repos/{repo.id}/logs/entities/ref:customer", expected_status_code=status_code
    )


async def test_get_logs_as_csv_minimal_log(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(
        log_write_client,
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )

    resp = await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/csv",
    )
    assert (
        resp.text
        == "log_id,saved_at,action_type,action_category,actor_ref,actor_type,actor_name,resource_ref,resource_type,resource_name,tag_ref,tag_type,tag_name,attachment_name,attachment_type,attachment_mime_type,entity_path:ref,entity_path:name\r\n"
        f"{log.id},2024-01-01T00:00:00Z,user-login,authentication,,,,,,,,,,,,,entity,Entity\r\n"
    )
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"


async def test_get_logs_as_csv_log_with_all_fields(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(
        log_rw_client,
        PreparedLog.prepare_data(
            {
                "actor": {
                    "type": "user",
                    "ref": "user:123",
                    "name": "User 123",
                },
                "resource": {
                    "ref": "core",
                    "type": "module",
                    "name": "Core Module",
                },
                "details": [
                    {"name": "some-key", "value": "some_value"},
                ],
                "tags": [
                    {
                        "type": "simple-tag",
                    },
                    {"ref": "rich_tag:1", "type": "rich-tag", "name": "Rich tag"},
                ],
            }
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )
    await log.upload_attachment(
        log_rw_client,
        name="attachment.txt",
        mime_type="text/plain",
        type="attachment-type",
    )

    resp = await log_rw_client.assert_get_ok(
        f"/repos/{repo.id}/logs/csv",
    )
    assert (
        resp.text
        == "log_id,saved_at,action_type,action_category,actor_ref,actor_type,actor_name,resource_ref,resource_type,resource_name,tag_ref,tag_type,tag_name,attachment_name,attachment_type,attachment_mime_type,entity_path:ref,entity_path:name\r\n"
        f"{log.id},2024-01-01T00:00:00Z,user-login,authentication,user:123,user,User 123,core,module,Core Module,|rich_tag:1,simple-tag|rich-tag,|Rich tag,attachment.txt,attachment-type,text/plain,entity,Entity\r\n"
    )


async def test_get_logs_as_csv_with_columns_param(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await repo.create_log(
        log_write_client,
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )

    resp = await log_read_client.assert_get_ok(
        f"/repos/{repo.id}/logs/csv",
        params={"columns": "saved_at,action_type,action_category"},
    )
    assert (
        resp.text == "saved_at,action_type,action_category\r\n"
        f"2024-01-01T00:00:00Z,user-login,authentication\r\n"
    )


async def test_get_logs_as_csv_with_columns_duplication(
    log_read_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await log_read_client.assert_get_bad_request(
        f"/repos/{repo.id}/logs/csv",
        params={"columns": "saved_at,action_type,action_type"},
    )


async def test_get_logs_as_csv_with_filter(
    log_rw_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log1 = await repo.create_log(
        log_rw_client,
        PreparedLog.prepare_data(
            {"action": {"category": "action-category-1", "type": "action-type-1"}}
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )
    log2 = await repo.create_log(
        log_rw_client,
        PreparedLog.prepare_data(
            {"action": {"category": "action-category-2", "type": "action-type-2"}}
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )

    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs/csv",
        params={"action_type": "action-type-1"},
    )
    assert (
        resp.text
        == "log_id,saved_at,action_type,action_category,actor_ref,actor_type,actor_name,resource_ref,resource_type,resource_name,tag_ref,tag_type,tag_name,attachment_name,attachment_type,attachment_mime_type,entity_path:ref,entity_path:name\r\n"
        f"{log1.id},2024-01-01T00:00:00Z,action-type-1,action-category-1,,,,,,,,,,,,,entity,Entity\r\n"
    )
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"


async def test_get_logs_as_csv_custom_fields(
    log_rw_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(
        log_rw_client,
        PreparedLog.prepare_data(
            {
                "source": [{"name": "source-field", "value": "source_value"}],
                "actor": {
                    "ref": "actor_ref",
                    "type": "actor",
                    "name": "Actor",
                    "extra": [{"name": "actor-field", "value": "actor_value"}],
                },
                "resource": {
                    "ref": "resource_ref",
                    "type": "resource",
                    "name": "Resource",
                    "extra": [{"name": "resource-field", "value": "resource_value"}],
                },
                "details": [{"name": "detail-field", "value": "detail_value"}],
            }
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )
    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs/csv",
        params={
            "columns": "log_id,source.source-field,actor.actor-field,resource.resource-field,details.detail-field"
        },
    )
    assert (
        resp.text
        == "log_id,source.source-field,actor.actor-field,resource.resource-field,details.detail-field\r\n"
        f"{log.id},source_value,actor_value,resource_value,detail_value\r\n"
    )
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"


async def test_get_logs_as_csv_with_csv_max_rows(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    # assume that AUDITIZE_CSV_MAX_ROWS is set to 10 in the test environment
    for _ in range(15):
        await repo.create_log(log_rw_client)

    resp = await log_rw_client.assert_get_ok(
        f"/repos/{repo.id}/logs/csv",
    )
    assert len(resp.text.splitlines()) == 11  # 10 logs + header


async def test_get_logs_as_csv_with_csv_max_rows_unlimited(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    for _ in range(15):
        await repo.create_log(log_rw_client)

    with patch("auditize.log.service.get_config") as mock:
        mock.return_value.csv_max_rows = 0
        resp = await log_rw_client.assert_get_ok(
            f"/repos/{repo.id}/logs/csv",
        )
    assert len(resp.text.splitlines()) == 16  # 15 logs + header


async def test_get_logs_as_csv_unknown_column(
    log_rw_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await log_rw_client.assert_get_bad_request(
        f"/repos/{repo.id}/logs/csv",
        params={
            "columns": "unknown_column",
        },
    )


async def test_get_logs_as_csv_unknown_custom_field(
    log_rw_client: HttpTestHelper,
    repo: PreparedRepo,
):
    # Requesting an unknown custom field column should not raise an error since they are lazy created
    await log_rw_client.assert_get_ok(
        f"/repos/{repo.id}/logs/csv",
        params={
            "columns": "source.unknown_column",
        },
    )


async def test_get_logs_as_csv_unknown_repo(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get_not_found(f"/repos/{UNKNOWN_UUID}/logs/csv")


async def test_get_logs_as_csv_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}/logs/csv")
