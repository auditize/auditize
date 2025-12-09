import base64
import json
from datetime import datetime
from unittest.mock import patch

import callee
import pytest

from conftest import ApikeyBuilder, RepoBuilder, UserBuilder
from helpers.http import HttpTestHelper
from helpers.log import UNKNOWN_UUID, PreparedLog
from helpers.pagination import (
    do_test_cursor_pagination_common_scenarios,
    do_test_cursor_pagination_empty_data,
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
    log_data = PreparedLog.prepare_data()
    await log_write_client.assert_post_created(
        f"/repos/{repo.id}/logs",
        json=log_data,
        expected_json=PreparedLog.build_expected_api_response(log_data),
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
    log_data = PreparedLog.prepare_data(
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
        json=log_data,
        expected_status_code=201,
        expected_json=PreparedLog.build_expected_api_response(log_data),
    )


async def test_create_log_all_fields_v0_9_0_backward_compatibility(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    """Test that we can create a log with identifiers that use hyphens (Auditize <= 0.9.0)"""

    log_data = PreparedLog.prepare_data(
        {
            "action": {
                "type": "user-login",
                "category": "user-authentication",
            },
            "source": [
                {"name": "ip-address", "value": "1.1.1.1"},
                {"name": "user-agent", "value": "Mozilla/5.0"},
            ],
            "actor": {
                "type": "user-account",
                "ref": "user:123",
                "name": "User 123",
                "extra": [{"name": "role", "value": "admin"}],
            },
            "resource": {
                "ref": "core",
                "type": "core-module",
                "name": "Core Module",
                "extra": [{"name": "creator-name", "value": "xyz"}],
            },
            "details": [
                {"name": "some-key", "value": "some_value"},
                {"name": "other-key", "value": "other_value"},
            ],
            "tags": [
                {
                    "type": "simple-tag",
                },
                {"ref": "rich-tag:1", "type": "rich-tag", "name": "Rich tag"},
            ],
        }
    )

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs",
        json=log_data,
        expected_status_code=201,
        expected_json=PreparedLog.build_expected_api_response(
            {
                **log_data,
                "action": {
                    "type": "user_login",
                    "category": "user_authentication",
                },
                "source": [
                    {"name": "ip_address", "value": "1.1.1.1"},
                    {"name": "user_agent", "value": "Mozilla/5.0"},
                ],
                "actor": {
                    "type": "user_account",
                    "ref": "user:123",
                    "name": "User 123",
                    "extra": [{"name": "role", "value": "admin"}],
                },
                "resource": {
                    "ref": "core",
                    "type": "core_module",
                    "name": "Core Module",
                    "extra": [{"name": "creator_name", "value": "xyz"}],
                },
                "details": [
                    {"name": "some_key", "value": "some_value"},
                    {"name": "other_key", "value": "other_value"},
                ],
                "tags": [
                    {
                        "type": "simple_tag",
                    },
                    {"ref": "rich-tag:1", "type": "rich_tag", "name": "Rich tag"},
                ],
            }
        ),
    )


@pytest.mark.parametrize(
    "custom_field",
    [
        {"name": "foo", "value": "bar", "type": "enum"},
        {"name": "enabled", "value": True, "type": "boolean"},
        {"name": "enabled", "value": True},
        {"name": "json", "value": '{"foo": "bar"}', "type": "json"},
        {"name": "integer", "value": 123, "type": "integer"},
        {"name": "integer", "value": 123},
        {"name": "float", "value": 123.45, "type": "float"},
        {"name": "float", "value": 123.45},
        {"name": "datetime", "value": "2021-01-01T00:00:00.000Z", "type": "datetime"},
    ],
)
async def test_create_log_typed_custom_fields(
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
    custom_field: dict,
):
    log_data = PreparedLog.prepare_data(
        {
            "source": [custom_field],
            "actor": {
                "type": "user",
                "ref": "user:123",
                "name": "User 123",
                "extra": [custom_field],
            },
            "resource": {
                "ref": "core",
                "type": "module",
                "name": "Core Module",
                "extra": [custom_field],
            },
            "details": [custom_field],
        }
    )

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs",
        json=log_data,
        expected_status_code=201,
        expected_json=PreparedLog.build_expected_api_response(log_data),
    )


@pytest.mark.parametrize(
    "field_name,field_value,field_type",
    [
        ("json", '{"foo": "bar"', "json"),
        ("boolean", "true", "boolean"),
        ("integer", "123", "integer"),
        ("float", "123.45", "float"),
        ("datetime", "not a valid datetime", "datetime"),
        ("enum", "not a valid enum", "enum"),
    ],
)
async def test_create_log_invalid_typed_custom_fields(
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
    field_name: str,
    field_value: str | int | dict | None,
    field_type: str,
):
    log_data = PreparedLog.prepare_data(
        {
            "source": [{"name": field_name, "value": field_value, "type": field_type}],
        }
    )

    await log_write_client.assert_post_bad_request(
        f"/repos/{repo.id}/logs", json=log_data
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
        "foo bar",
    ):
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


async def test_create_log_can_have_entities_with_same_name_but_different_parents(
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


async def test_create_log_can_have_entities_with_same_name_and_parent_in_different_repos(
    log_write_client: HttpTestHelper,
    repo_builder: RepoBuilder,
):
    """Check that we can create a log with the same entity name (but different refs) twice at the same level in different repos"""

    repo1 = await repo_builder({"name": "Repo 1"})
    repo2 = await repo_builder({"name": "Repo 2"})

    await log_write_client.assert_post_created(
        f"/repos/{repo1.id}/logs",
        json=PreparedLog.prepare_data(
            {
                "entity_path": [
                    {"ref": "Entity A", "name": "Entity A"},
                    {"ref": "Entity B", "name": "Entity B"},
                ]
            }
        ),
    )

    await log_write_client.assert_post_created(
        f"/repos/{repo2.id}/logs",
        json=PreparedLog.prepare_data(
            {
                "entity_path": [
                    {"ref": "Entity A", "name": "Entity A"},
                    {"ref": "Another ref for Entity B", "name": "Entity B"},
                ]
            }
        ),
    )


async def test_create_log_from_openapi_example(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    # Payload example generated by Redoc for Auditize 0.3.0
    log = json.loads("""{
  "action": {
    "type": "create_configuration_profile",
    "category": "configuration"
  },
  "source": [
    {
      "name": "ip",
      "value": "127.0.0.1"
    },
    {
      "name": "user_agent",
      "value": "Mozilla/5.0"
    }
  ],
  "actor": {
    "ref": "user:123",
    "type": "user",
    "name": "John Doe",
    "extra": [
      {
        "name": "role",
        "value": "admin"
      }
    ]
  },
  "resource": {
    "ref": "config-profile:123",
    "type": "config_profile",
    "name": "Config Profile 123",
    "extra": [
      {
        "name": "description",
        "value": "Description of the configuration profile"
      }
    ]
  },
  "details": [
    {
      "name": "field_name_1",
      "value": "value 1"
    },
    {
      "name": "field_name_2",
      "value": "value 2"
    }
  ],
  "tags": [
    {
      "type": "security"
    }
  ],
  "entity_path": [
    {
      "name": "Customer 1",
      "ref": "customer:1"
    },
    {
      "name": "Entity 1",
      "ref": "entity:1"
    }
  ]
}""")
    await repo.create_log(log_write_client, log)


async def test_import_log_no_extra_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    log_data = PreparedLog.prepare_data()
    await log_write_client.assert_post_created(
        f"/repos/{repo.id}/logs/import",
        json=log_data,
        expected_json=PreparedLog.build_expected_api_response(log_data),
    )


async def test_import_log_with_extra_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    log_data = PreparedLog.prepare_data(
        {
            "id": UNKNOWN_UUID,
            "saved_at": "2021-01-01T00:00:00.000Z",
        }
    )
    await log_write_client.assert_post_created(
        f"/repos/{repo.id}/logs/import",
        json=log_data,
        expected_json=PreparedLog.build_expected_api_response(log_data),
    )


async def test_import_log_id_already_used(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    existing_log = await repo.create_log(log_write_client)
    imported_log_data = PreparedLog.prepare_data(
        {
            "id": existing_log.id,
        }
    )
    await log_write_client.assert_post_constraint_violation(
        f"/repos/{repo.id}/logs/import",
        json=imported_log_data,
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


async def test_get_log_forbidden_entity(
    superadmin_client: HttpTestHelper, repo: PreparedRepo, apikey_builder: ApikeyBuilder
):
    log_1 = await repo.create_log_with_entity_path(superadmin_client, ["entity_A"])
    log_2 = await repo.create_log_with_entity_path(superadmin_client, ["entity_B"])
    apikey = await apikey_builder(
        {
            "logs": {
                "repos": [
                    {
                        "repo_id": repo.id,
                        "readable_entities": ["entity_A"],
                    }
                ]
            }
        }
    )
    async with apikey.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(f"/repos/{repo.id}/logs/{log_1.id}")
        await client.assert_get_not_found(f"/repos/{repo.id}/logs/{log_2.id}")


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
        data={"type": "text_file"},
        expected_status_code=204,
    )

    await no_permission_client.assert_get_forbidden(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )


async def test_get_log_attachment_forbidden_entity(
    superadmin_client: HttpTestHelper, repo: PreparedRepo, apikey_builder: ApikeyBuilder
):
    log_1 = await repo.create_log_with_entity_path(superadmin_client, ["entity_A"])
    await log_1.upload_attachment(superadmin_client)
    log_2 = await repo.create_log_with_entity_path(superadmin_client, ["entity_B"])
    await log_2.upload_attachment(superadmin_client)
    apikey = await apikey_builder(
        {
            "logs": {
                "repos": [
                    {
                        "repo_id": repo.id,
                        "readable_entities": ["entity_A"],
                    }
                ]
            }
        }
    )

    async with apikey.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(f"/repos/{repo.id}/logs/{log_1.id}/attachments/0")
        await client.assert_get_not_found(
            f"/repos/{repo.id}/logs/{log_2.id}/attachments/0"
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
        data={"type": "text_file"},
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
    await log_read_client.assert_get_not_found(f"/repos/{UNKNOWN_UUID}/logs")


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
    logs = [await repo.create_log(log_rw_client) for _ in range(5)]

    await do_test_cursor_pagination_common_scenarios(
        log_rw_client,
        f"/repos/{repo.id}/logs",
        items=[log.expected_api_response() for log in reversed(logs)],
    )


async def _test_get_logs_filter(
    client: HttpTestHelper,
    repo: PreparedRepo,
    search_params: dict,
    expected_log: PreparedLog,
    *,
    extra_log=True,
):
    # Create a log that is not supposed to be returned, it ensures that the request
    # does not simply return all logs
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
        log_rw_client, {"action": {"category": "category", "type": "find_me"}}
    )

    await _test_get_logs_filter(log_rw_client, repo, {"action_type": "find_me"}, log)


async def test_get_logs_filter_action_category(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client, {"action": {"category": "find_me", "type": "type"}}
    )

    await _test_get_logs_filter(
        log_rw_client, repo, {"action_category": "find_me"}, log
    )


async def test_get_logs_filter_actor_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"actor": {"type": "find_me", "ref": "user:123", "name": "User 123"}},
    )

    await _test_get_logs_filter(log_rw_client, repo, {"actor_type": "find_me"}, log)


async def test_get_logs_filter_actor_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "user:123", "name": "find_me"}}
    )

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"actor_name": "find_me"}, log)


async def test_get_logs_filter_actor_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "user:123", "name": "find_me"}}
    )

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"actor_ref": "user:123"}, log)


async def test_get_logs_filter_resource_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"resource": {"ref": "core", "type": "find_me", "name": "Core Module"}},
    )

    await _test_get_logs_filter(log_rw_client, repo, {"resource_type": "find_me"}, log)


async def test_get_logs_filter_resource_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"resource": {"ref": "core", "type": "module", "name": "find_me"}},
    )

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"resource_name": "find_me"}, log)


async def test_get_logs_filter_resource_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {"resource": {"ref": "core", "type": "module", "name": "find_me"}},
    )

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"resource_ref": "core"}, log)


class _DetailsCustomFieldsMixin:
    field_prefix = "details"
    relative_path = "details"

    def prepare_log_data(self, fields: list[dict]) -> dict:
        return PreparedLog.prepare_data({"details": fields})


class _SourceCustomFieldsMixin:
    field_prefix = "source"
    relative_path = "source"

    def prepare_log_data(self, fields: list[dict]) -> dict:
        return PreparedLog.prepare_data({"source": fields})


class _ResourceExtraCustomFieldsMixin:
    field_prefix = "resource"
    relative_path = "resources/extras"

    def prepare_log_data(self, fields: list[dict]) -> dict:
        return PreparedLog.prepare_data(
            {
                "resource": {
                    "type": "config_profile",
                    "ref": "config-profile:123",
                    "name": "Config Profile 123",
                    "extra": fields,
                }
            }
        )


class _ActorExtraCustomFieldsMixin:
    field_prefix = "actor"
    relative_path = "actors/extras"

    def prepare_log_data(self, fields: list[dict]) -> dict:
        return PreparedLog.prepare_data(
            {
                "actor": {
                    "type": "user",
                    "ref": "12345",
                    "name": "John Doe",
                    "extra": fields,
                }
            }
        )


class _TestGetLogsFilterCustomField:
    def prepare_log_data(self, custom_fields: list[dict[str, str]]) -> dict:
        raise NotImplementedError

    @property
    def field_prefix(self) -> str:
        raise NotImplementedError

    @pytest.mark.parametrize(
        "matching_fields,non_matching_fields,filter_params",
        [
            # string
            (
                [
                    {"name": "field_1", "value": "foo something"},
                    {"name": "field_2", "value": "bar something else"},
                ],
                [
                    {"name": "field_1", "value": "bar something"},
                    {"name": "field_2", "value": "foo something else"},
                ],
                {
                    "field_1": "something foo",
                    "field_2": "something bar",
                },
            ),
            # enum
            (
                [{"name": "status", "value": "enabled", "type": "enum"}],
                [{"name": "status", "value": "disabled", "type": "enum"}],
                {"status": "enabled"},
            ),
            # boolean - True
            (
                [{"name": "enabled", "value": True, "type": "boolean"}],
                [{"name": "enabled", "value": False, "type": "boolean"}],
                {"enabled": True},
            ),
            # boolean - False
            (
                [{"name": "enabled", "value": False, "type": "boolean"}],
                [{"name": "enabled", "value": True, "type": "boolean"}],
                {"enabled": False},
            ),
            # json
            (
                [{"name": "data", "value": '{"foo": "bar"}', "type": "json"}],
                [{"name": "data", "value": '{"foo": "baz"}', "type": "json"}],
                {"data": "foo bar"},
            ),
            # integer
            (
                [{"name": "data", "value": 123, "type": "integer"}],
                [{"name": "data", "value": 456, "type": "integer"}],
                {"data": 123},
            ),
            # float
            (
                [{"name": "data", "value": 123.45, "type": "float"}],
                [{"name": "data", "value": 456.78, "type": "float"}],
                {"data": 123.45},
            ),
            # datetime
            (
                [
                    {
                        "name": "data",
                        "value": "2021-01-01T00:00:00.000Z",
                        "type": "datetime",
                    }
                ],
                [
                    {
                        "name": "data",
                        "value": "2021-01-01T01:00:00.000Z",
                        "type": "datetime",
                    }
                ],
                {"data": "2021-01-01T00:00:00.000Z"},
            ),
        ],
    )
    async def test_field_types(
        self,
        log_rw_client: HttpTestHelper,
        repo: PreparedRepo,
        matching_fields: list[dict],
        non_matching_fields: list[dict],
        filter_params: dict,
    ):
        matching_log = await repo.create_log(
            log_rw_client,
            self.prepare_log_data(matching_fields),
        )
        await repo.create_log(
            log_rw_client,
            self.prepare_log_data(non_matching_fields),
        )

        await _test_get_logs_filter(
            client=log_rw_client,
            repo=repo,
            search_params={
                f"{self.field_prefix}.{key}": value
                for key, value in filter_params.items()
            },
            expected_log=matching_log,
            extra_log=False,
        )

    @pytest.mark.parametrize(
        "field_type,valid_value",
        [
            ("boolean", True),
            ("integer", 123),
            ("float", 123.45),
            ("datetime", "2021-01-01T00:00:00.000Z"),
        ],
    )
    async def test_invalid_field_values(
        self,
        log_rw_client: HttpTestHelper,
        repo: PreparedRepo,
        field_type: str,
        valid_value: str,
    ):
        # Create a log with a valid value so that Auditize knows about the field type
        await repo.create_log(
            log_rw_client,
            self.prepare_log_data(
                [{"name": field_type, "value": valid_value, "type": field_type}]
            ),
        )

        # Check that invalid values are rejected
        await log_rw_client.assert_get_bad_request(
            f"/repos/{repo.id}/logs",
            params={
                f"{self.field_prefix}.{field_type}": "INVALID VALUE",
            },
        )


class TestGetLogsFilterSource(_SourceCustomFieldsMixin, _TestGetLogsFilterCustomField):
    pass


class TestGetLogsFilterDetails(
    _DetailsCustomFieldsMixin, _TestGetLogsFilterCustomField
):
    pass


class TestGetLogsFilterResourceExtra(
    _ResourceExtraCustomFieldsMixin, _TestGetLogsFilterCustomField
):
    pass


class TestGetLogsFilterActorExtra(
    _ActorExtraCustomFieldsMixin, _TestGetLogsFilterCustomField
):
    pass


async def test_get_logs_filter_tag_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "simple_tag"},
                {"ref": "rich_tag:1", "type": "find_me", "name": "Rich tag"},
            ]
        },
    )

    await _test_get_logs_filter(log_rw_client, repo, {"tag_type": "find_me"}, log)


async def test_get_logs_filter_tag_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "simple_tag"},
                {"ref": "rich_tag:1", "type": "rich_tag", "name": "find_me"},
            ]
        },
    )

    # filter on tag_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, {"tag_name": "find_me"}, log)


async def test_get_logs_filter_tag_ref(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "simple_tag"},
                {"ref": "find_me", "type": "rich_tag", "name": "Rich tag"},
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
        name="foo bar something.txt",
        type="text",
        mime_type="text/plain",
    )
    await _test_get_logs_filter(
        log_rw_client, repo, {"attachment_name": "foo bar something.txt"}, log
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
        log_rw_client, repo, {"attachment_type": "find_me"}, log
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


class _TestGetLogsFullTextSearchCustomField:
    def prepare_log_data(self, custom_fields: list[dict[str, str]]) -> dict:
        raise NotImplementedError

    async def test_nominal(self, log_rw_client: HttpTestHelper, repo: PreparedRepo):
        matching_log = await repo.create_log_with(
            log_rw_client,
            self.prepare_log_data(
                [
                    {
                        "name": "param1",
                        # NB: ensure case-insensitive search
                        "value": "FOO",
                    },
                    {
                        "name": "param2",
                        # NB: ensure accent-insensitive search
                        "value": "barré",
                    },
                ]
            ),
        )
        non_matching_log = await repo.create_log_with(
            log_rw_client,
            {
                "source": [
                    {
                        "name": "param1",
                        "value": "foo",
                    },
                ],
            },
        )
        await _test_get_logs_filter(
            log_rw_client, repo, {"q": "foo barre"}, matching_log
        )


class TestGetLogsFullTextSearchSource(
    _SourceCustomFieldsMixin, _TestGetLogsFullTextSearchCustomField
):
    pass


class TestGetLogsFullTextSearchActorExtra(
    _ActorExtraCustomFieldsMixin, _TestGetLogsFullTextSearchCustomField
):
    pass


class TestGetLogsFullTextSearchResourceExtra(
    _ResourceExtraCustomFieldsMixin, _TestGetLogsFullTextSearchCustomField
):
    pass


class TestGetLogsFullTextSearchDetails(
    _DetailsCustomFieldsMixin, _TestGetLogsFullTextSearchCustomField
):
    pass


async def test_get_logs_full_text_search_resource_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log_with(
        log_rw_client,
        {
            "resource": {
                "name": "foo something bar",
                "ref": "config-profile:123",
                "type": "config_profile",
            },
        },
    )
    await _test_get_logs_filter(log_rw_client, repo, {"q": "foo bar"}, log)


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
        {"since": "2024-01-01T12:00:00.000Z"},
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
        {"until": "2024-01-01T12:00:00.000Z"},
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
        {"until": "2023-12-31T23:59:59.999Z"},
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
        {"since": "2024-01-01T12:00:00.000Z", "until": "2024-01-02T12:00:00.000Z"},
        log2,
        extra_log=False,
    )


async def test_get_logs_filter_multiple_criteria(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log_1 = await repo.create_log_with(
        log_rw_client,
        {
            "action": {"type": "find_me_action_type", "category": "category"},
        },
    )

    log_2 = await repo.create_log_with(
        log_rw_client,
        {
            "action": {"type": "type", "category": "find_me_action_category"},
        },
    )

    log_3 = await repo.create_log_with(
        log_rw_client,
        {
            "action": {
                "type": "find_me_action_type",
                "category": "find_me_action_category",
            },
        },
    )

    await _test_get_logs_filter(
        log_rw_client,
        repo,
        {
            "action_type": "find_me_action_type",
            "action_category": "find_me_action_category",
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
                        "read": False if authorized_entities else True,
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
                        "read": False if authorized_entities else True,
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
                "pagination": {"next_cursor": None},
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


async def test_get_log_entities_multiple_repos(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo1 = await repo_builder({"name": "Repo 1"})
    repo2 = await repo_builder({"name": "Repo 2"})

    await repo1.create_log_with_entity_path(superadmin_client, ["Entity A"])
    await repo2.create_log_with_entity_path(superadmin_client, ["Entity B"])

    await superadmin_client.assert_get_ok(
        f"/repos/{repo1.id}/logs/entities",
        expected_json={
            "items": [
                {
                    "ref": "Entity A",
                    "name": "Entity A",
                    "parent_entity_ref": None,
                    "has_children": False,
                },
            ],
            "pagination": {"next_cursor": None},
        },
    )
    await superadmin_client.assert_get_ok(
        f"/repos/{repo2.id}/logs/entities",
        expected_json={
            "items": [
                {
                    "ref": "Entity B",
                    "name": "Entity B",
                    "parent_entity_ref": None,
                    "has_children": False,
                },
            ],
            "pagination": {"next_cursor": None},
        },
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
                        "read": False if authorized_entities else True,
                        "readable_entities": authorized_entities,
                    }
                ]
            }
        }
    )

    async with apikey.client() as client:
        if expected_status_code == 200:
            await client.assert_get_ok(
                f"/repos/{repo.id}/logs/entities/{entity_ref}",
                expected_json={
                    "ref": entity_ref,
                    "name": entity_ref,
                    "parent_entity_ref": callee.OneOf(callee.Eq(None), callee.IsA(str)),
                    "has_children": callee.IsA(bool),
                },
            )
        else:
            await client.assert_get(
                f"/repos/{repo.id}/logs/entities/{entity_ref}",
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


async def test_get_log_entity_multiple_repos(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    # Create two repos with different entities

    repo1 = await repo_builder({"name": "Repo 1"})
    repo2 = await repo_builder({"name": "Repo 2"})

    await repo1.create_log_with_entity_path(superadmin_client, ["Entity A"])
    await repo2.create_log_with_entity_path(superadmin_client, ["Entity B"])

    # Make sure that Entity A is only visible in Repo 1
    # and Entity B is only visible in Repo 2

    await superadmin_client.assert_get_ok(
        f"/repos/{repo1.id}/logs/entities/Entity A",
        expected_json={
            "ref": "Entity A",
            "name": "Entity A",
            "parent_entity_ref": None,
            "has_children": False,
        },
    )
    await superadmin_client.assert_get_not_found(
        f"/repos/{repo2.id}/logs/entities/Entity A",
    )
    await superadmin_client.assert_get_ok(
        f"/repos/{repo2.id}/logs/entities/Entity B",
        expected_json={
            "ref": "Entity B",
            "name": "Entity B",
            "parent_entity_ref": None,
            "has_children": False,
        },
    )
    await superadmin_client.assert_get_not_found(
        f"/repos/{repo1.id}/logs/entities/Entity B",
    )


class _ConsolidatedDataTest:
    @property
    def relative_path(self) -> str:
        raise NotImplementedError()

    def get_path(self, repo_id: str) -> str:
        return f"/repos/{repo_id}/logs/aggs/{self.relative_path}"

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
        await do_test_cursor_pagination_common_scenarios(
            log_read_client,
            self.get_path(repo.id),
            items=[{"name": item} for item in reversed(items)],
        )

    async def test_empty(self, log_read_client: HttpTestHelper, repo: PreparedRepo):
        await do_test_cursor_pagination_empty_data(
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
            f"/repos/{repo.id}/logs/aggs/actions/types?category=category_2",
            expected_json={
                "items": [{"name": f"type_{2}"}],
                "pagination": {"next_cursor": None},
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


class _ConsolidatedNameRefPairsTest:
    @property
    def data_type(self) -> str:
        raise NotImplementedError()

    def get_path(self, repo_id: str) -> str:
        return f"/repos/{repo_id}/logs/aggs/{self.data_type}s/names"

    async def test_nominal(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        # A: create 3 logs with the same ref but different names
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {"name": "Data A", "ref": "data:A", "type": "data"},
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {"name": "Data A", "ref": "data:A", "type": "data"},
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {"name": "Data A bis", "ref": "data:A", "type": "data"},
            },
        )

        # B: create a single log
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {"name": "Data B", "ref": "data:B", "type": "data"},
            },
        )

        # C: create two logs with the same name but different refs
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {"name": "Data C", "ref": "data:C", "type": "data"},
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {
                    "name": "Data C bis",
                    "ref": "data:C:bis",
                    "type": "data",
                },
            },
        )

        # Assert that data names and refs are correctly returned
        expected_items = [
            {"name": "Data A", "ref": "data:A"},
            {"name": "Data A bis", "ref": "data:A"},
            {"name": "Data B", "ref": "data:B"},
            {"name": "Data C", "ref": "data:C"},
            {"name": "Data C bis", "ref": "data:C:bis"},
        ]
        await do_test_cursor_pagination_common_scenarios(
            log_read_client,
            self.get_path(repo.id),
            items=expected_items,
        )

    async def test_query(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {
                    "name": "foo bar something",
                    "ref": "A",
                    "type": "data",
                },
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                self.data_type: {
                    "name": "bar something else",
                    "ref": "B",
                    "type": "data",
                },
            },
        )
        await log_read_client.assert_get_ok(
            self.get_path(repo.id),
            params={"q": "foo some"},
            expected_json={
                "items": [
                    {"name": "foo bar something", "ref": "A"},
                ],
                "pagination": {"next_cursor": None},
            },
        )

    async def test_empty(self, log_read_client: HttpTestHelper, repo: PreparedRepo):
        await do_test_cursor_pagination_empty_data(
            log_read_client, self.get_path(repo.id)
        )

    async def test_not_found(self, log_read_client: HttpTestHelper):
        await log_read_client.assert_get_not_found(self.get_path(UNKNOWN_UUID))

    async def test_forbidden(
        self, no_permission_client: HttpTestHelper, repo: PreparedRepo
    ):
        await no_permission_client.assert_get_forbidden(self.get_path(repo.id))


class TestLogActorNames(_ConsolidatedNameRefPairsTest):
    data_type = "actor"


class TestLogResourceNames(_ConsolidatedNameRefPairsTest):
    data_type = "resource"


class TestLogTagNames(_ConsolidatedNameRefPairsTest):
    data_type = "tag"

    async def test_nominal(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        # A: create 3 logs with the same ref but different names
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [{"name": "Data A", "ref": "data:A", "type": "data"}],
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [{"name": "Data A", "ref": "data:A", "type": "data"}],
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [{"name": "Data A bis", "ref": "data:A", "type": "data"}],
            },
        )

        # B: create a single log
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [
                    {"name": "Data B", "ref": "data:B", "type": "data"},
                    {"name": "Data A", "ref": "data:A", "type": "data"},
                ],
            },
        )

        # C: create two logs with the same name but different refs
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [
                    {"name": "Data C", "ref": "data:C", "type": "data"},
                    {"name": "Data B", "ref": "data:B", "type": "data"},
                    {"name": "Data A", "ref": "data:A", "type": "data"},
                ],
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [
                    {"name": "Data C bis", "ref": "data:C:bis", "type": "data"},
                    {"name": "Data B", "ref": "data:B", "type": "data"},
                    {"name": "Data A", "ref": "data:A", "type": "data"},
                ],
            },
        )

        # Assert that data names and refs are correctly returned
        expected_items = [
            {"name": "Data A", "ref": "data:A"},
            {"name": "Data A bis", "ref": "data:A"},
            {"name": "Data B", "ref": "data:B"},
            {"name": "Data C", "ref": "data:C"},
            {"name": "Data C bis", "ref": "data:C:bis"},
        ]
        await do_test_cursor_pagination_common_scenarios(
            log_read_client,
            self.get_path(repo.id),
            items=expected_items,
        )

    async def test_query(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [{"name": "foo bar something", "ref": "A", "type": "data"}],
            },
        )
        await repo.create_log_with(
            superadmin_client,
            {
                "tags": [{"name": "bar something else", "ref": "B", "type": "data"}],
            },
        )
        await log_read_client.assert_get_ok(
            self.get_path(repo.id),
            params={"q": "foo some"},
            expected_json={
                "items": [
                    {"name": "foo bar something", "ref": "A"},
                ],
                "pagination": {"next_cursor": None},
            },
        )


class _TestGetSubElementByRef:
    def get_path(self, repo_id: str, ref: str) -> str:
        raise NotImplementedError

    async def create_log(
        self, superadmin_client: HttpTestHelper, repo: PreparedRepo, *, ref: str
    ):
        raise NotImplementedError

    def build_expected_json(self, *, ref: str) -> dict:
        raise NotImplementedError

    async def test_nominal(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        await self.create_log(superadmin_client, repo, ref="A")
        await log_read_client.assert_get_ok(
            self.get_path(repo.id, "A"),
            expected_json=self.build_expected_json(ref="A"),
        )

    async def test_not_found(self, log_read_client: HttpTestHelper, repo: PreparedRepo):
        await log_read_client.assert_get_not_found(self.get_path(repo.id, "A"))

    async def test_forbidden(
        self,
        superadmin_client: HttpTestHelper,
        no_permission_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        await self.create_log(superadmin_client, repo, ref="A")
        await no_permission_client.assert_get_forbidden(self.get_path(repo.id, "A"))


class TestLogActor(_TestGetSubElementByRef):
    def get_path(self, repo_id: str, ref: str) -> str:
        return f"/repos/{repo_id}/logs/actors/{ref}"

    async def create_log(
        self, superadmin_client: HttpTestHelper, repo: PreparedRepo, *, ref: str
    ):
        await repo.create_log_with(
            superadmin_client,
            {"actor": {"ref": ref, "name": f"Name of {ref}", "type": "data"}},
        )

    def build_expected_json(self, *, ref: str) -> dict:
        return {
            "ref": ref,
            "name": f"Name of {ref}",
            "type": "data",
            "extra": [],
        }


class TestLogResource(_TestGetSubElementByRef):
    def get_path(self, repo_id: str, ref: str) -> str:
        return f"/repos/{repo_id}/logs/resources/{ref}"

    async def create_log(
        self, superadmin_client: HttpTestHelper, repo: PreparedRepo, *, ref: str
    ):
        await repo.create_log_with(
            superadmin_client,
            {"resource": {"ref": ref, "name": f"Name of {ref}", "type": "data"}},
        )

    def build_expected_json(self, *, ref: str) -> dict:
        return {
            "ref": ref,
            "name": f"Name of {ref}",
            "type": "data",
            "extra": [],
        }


class TestLogTag(_TestGetSubElementByRef):
    def get_path(self, repo_id: str, ref: str) -> str:
        return f"/repos/{repo_id}/logs/tags/{ref}"

    async def create_log(
        self, superadmin_client: HttpTestHelper, repo: PreparedRepo, *, ref: str
    ):
        await repo.create_log_with(
            superadmin_client,
            {"tags": [{"ref": ref, "name": f"Name of {ref}", "type": "data"}]},
        )

    def build_expected_json(self, *, ref: str) -> dict:
        return {
            "ref": ref,
            "name": f"Name of {ref}",
            "type": "data",
        }


class _ConsolidatedCustomFieldsTest:
    @property
    def relative_path(self) -> str:
        raise NotImplementedError()

    def get_path(self, repo_id: str) -> str:
        return f"/repos/{repo_id}/logs/{self.relative_path}"

    def prepare_log_data(self, fields: list[dict]) -> dict:
        raise NotImplementedError()

    async def test_nominal(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        fields = [
            {
                "name": "field_1",
                "value": "Value 1",
                "type": "string",
            },
            {
                "name": "field_2",
                "value": "Value 2",
                "type": "string",
            },
            {
                "name": "field_3",
                "value": "Value 3",
                "type": "string",
            },
            {
                "name": "field_4",
                "value": "value_2",
                "type": "enum",
            },
            {
                "name": "field_5",
                "value": "value_3",
                "type": "enum",
            },
        ]
        for field in fields:
            await repo.create_log(superadmin_client, self.prepare_log_data([field]))
        await do_test_cursor_pagination_common_scenarios(
            log_read_client,
            self.get_path(repo.id),
            items=[{"name": field["name"], "type": field["type"]} for field in fields],
        )

    async def test_empty(self, log_read_client: HttpTestHelper, repo: PreparedRepo):
        await do_test_cursor_pagination_empty_data(
            log_read_client, self.get_path(repo.id)
        )

    async def test_not_found(self, log_read_client: HttpTestHelper):
        await log_read_client.assert_get_not_found(self.get_path(UNKNOWN_UUID))

    async def test_forbidden(
        self, no_permission_client: HttpTestHelper, repo: PreparedRepo
    ):
        await no_permission_client.assert_get_forbidden(self.get_path(repo.id))


class TestLogDetailsFields(_DetailsCustomFieldsMixin, _ConsolidatedCustomFieldsTest):
    pass


class TestLogSourceFields(_SourceCustomFieldsMixin, _ConsolidatedCustomFieldsTest):
    pass


class TestLogActorExtraFields(
    _ActorExtraCustomFieldsMixin, _ConsolidatedCustomFieldsTest
):
    pass


class TestLogResourceExtraFields(
    _ResourceExtraCustomFieldsMixin, _ConsolidatedCustomFieldsTest
):
    pass


class _CustomFieldsEnumValuesTest:
    @property
    def relative_path(self) -> str:
        raise NotImplementedError()

    def get_path(self, repo_id: str, field_name: str) -> str:
        return f"/repos/{repo_id}/logs/{self.relative_path}/{field_name}/values"

    def prepare_log_data(self, fields: list[dict]) -> dict:
        raise NotImplementedError()

    async def test_nominal(
        self,
        superadmin_client: HttpTestHelper,
        log_read_client: HttpTestHelper,
        repo: PreparedRepo,
    ):
        field_values = [f"value_{i + 1}" for i in range(5)]
        for value in field_values:
            for _ in range(2):
                # Create two logs for each value to ensure we get the distinct values
                await repo.create_log(
                    superadmin_client,
                    self.prepare_log_data(
                        [{"name": "my_field", "value": value, "type": "enum"}]
                    ),
                )
        await do_test_cursor_pagination_common_scenarios(
            log_read_client,
            self.get_path(repo.id, "my_field"),
            items=[{"value": value} for value in field_values],
        )

    async def test_empty(self, log_read_client: HttpTestHelper, repo: PreparedRepo):
        await do_test_cursor_pagination_empty_data(
            log_read_client, self.get_path(repo.id, "my_field")
        )

    async def test_not_found(self, log_read_client: HttpTestHelper):
        await log_read_client.assert_get_not_found(
            self.get_path(UNKNOWN_UUID, "my_field")
        )

    async def test_forbidden(
        self, no_permission_client: HttpTestHelper, repo: PreparedRepo
    ):
        await no_permission_client.assert_get_forbidden(
            self.get_path(repo.id, "my_field")
        )


class TestLogDetailsFieldsEnumValues(
    _DetailsCustomFieldsMixin, _CustomFieldsEnumValuesTest
):
    pass


class TestLogSourceFieldsEnumValues(
    _SourceCustomFieldsMixin, _CustomFieldsEnumValuesTest
):
    pass


class TestLogResourceExtraFieldsEnumValues(
    _ResourceExtraCustomFieldsMixin, _CustomFieldsEnumValuesTest
):
    pass


class TestLogActorExtraFieldsEnumValues(
    _ActorExtraCustomFieldsMixin, _CustomFieldsEnumValuesTest
):
    pass


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
    await superadmin_client.assert_get_ok(
        f"/repos/{repo.id}/logs/entities/A",
        expected_json={
            "ref": "A",
            "name": "Name of A",
            "parent_entity_ref": None,
            "has_children": True,
        },
    )
    await superadmin_client.assert_get_ok(
        f"/repos/{repo.id}/logs/entities/AA",
        expected_json={
            "ref": "AA",
            "name": "New name of AA",
            "parent_entity_ref": "A",
            "has_children": False,
        },
    )


async def test_log_entity_consolidation_move_entity(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log_with_entity_path(superadmin_client, ["A", "AA"])
    await repo.create_log_with_entity_path(superadmin_client, ["B"])
    await repo.create_log_with_entity_path(superadmin_client, ["B", "AA"])

    # Check that the entity AA is now a child of B
    await superadmin_client.assert_get_ok(
        f"/repos/{repo.id}/logs/entities",
        expected_json={
            "items": [
                {
                    "ref": "A",
                    "name": "A",
                    "parent_entity_ref": None,
                    "has_children": False,
                },
                {
                    "ref": "AA",
                    "name": "AA",
                    "parent_entity_ref": "B",
                    "has_children": False,
                },
                {
                    "ref": "B",
                    "name": "B",
                    "parent_entity_ref": None,
                    "has_children": True,
                },
            ],
            "pagination": {"next_cursor": None},
        },
    )


@pytest.mark.parametrize(
    "path",
    [
        "/logs",
        "/logs/aggs/actions/categories",
        "/logs/aggs/actions/types",
        "/logs/aggs/actors/types",
        "/logs/aggs/resources/types",
        "/logs/aggs/tags/types",
        "/logs/aggs/attachments/types",
        "/logs/aggs/attachments/mime-types",
        "/logs/details",
        "/logs/source",
        "/logs/resources/extras",
        "/logs/actors/extras",
        "/logs/details/my_field/values",
        "/logs/source/my_field/values",
        "/logs/resources/extras/my_field/values",
        "/logs/actors/extras/my_field/values",
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
    await do_test_cursor_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/entities",
        params={"root": "true"},
        items=[
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
    await do_test_cursor_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/entities",
        params={"parent_entity_ref": "customer:2"},
        items=[
            {
                "ref": f"entity:2-{j}",
                "name": f"Entity {j}",
                "parent_entity_ref": "customer:2",
                "has_children": False,
            }
            for j in ("a", "b", "c", "d", "e")
        ],
    )


async def test_get_log_entities_empty(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await do_test_cursor_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/entities?root=true"
    )


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
        f"/repos/{repo.id}/logs/entities/customer",
        expected_json={
            "ref": "customer",
            "name": "Customer",
            "parent_entity_ref": None,
            "has_children": True,
        },
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/entities/entity",
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
        f"/repos/{repo.id}/logs/entities/some_value"
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
        f"/repos/{repo.id}/logs/entities/customer", expected_status_code=status_code
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

    resp = await log_read_client.assert_get(f"/repos/{repo.id}/logs/csv")
    assert (
        resp.text
        == "Log ID,Date,Action Type,Action Category,Actor Ref,Actor Type,Actor Name,Resource Ref,Resource Type,Resource Name,Tag Ref,Tag Type,Tag Name,Attachment Name,Attachment Type,Attachment MIME Type,Entity Refs,Entity Names\r\n"
        f"{log.id},2024-01-01T00:00:00.000Z,User Login,Authentication,,,,,,,,,,,,,entity,Entity\r\n"
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
                    {"name": "some_key", "value": "some_value"},
                ],
                "tags": [
                    {
                        "type": "simple_tag",
                    },
                    {"ref": "rich_tag:1", "type": "rich_tag", "name": "Rich tag"},
                ],
            }
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )
    await log.upload_attachment(
        log_rw_client,
        name="attachment.txt",
        mime_type="text/plain",
        type="attachment_type",
    )

    resp = await log_rw_client.assert_get_ok(f"/repos/{repo.id}/logs/csv")
    assert (
        resp.text
        == "Log ID,Date,Action Type,Action Category,Actor Ref,Actor Type,Actor Name,Resource Ref,Resource Type,Resource Name,Tag Ref,Tag Type,Tag Name,Attachment Name,Attachment Type,Attachment MIME Type,Entity Refs,Entity Names\r\n"
        f"{log.id},2024-01-01T00:00:00.000Z,User Login,Authentication,user:123,User,User 123,core,Module,Core Module,|rich_tag:1,Simple Tag|Rich Tag,|Rich tag,attachment.txt,Attachment Type,text/plain,entity,Entity\r\n"
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
        resp.text == "Date,Action Type,Action Category\r\n"
        f"2024-01-01T00:00:00.000Z,User Login,Authentication\r\n"
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
            {"action": {"category": "action_category_1", "type": "action_type_1"}}
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )
    log2 = await repo.create_log(
        log_rw_client,
        PreparedLog.prepare_data(
            {"action": {"category": "action_category_2", "type": "action_type_2"}}
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )

    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs/csv",
        params={"action_type": "action_type_1"},
    )
    assert (
        resp.text
        == "Log ID,Date,Action Type,Action Category,Actor Ref,Actor Type,Actor Name,Resource Ref,Resource Type,Resource Name,Tag Ref,Tag Type,Tag Name,Attachment Name,Attachment Type,Attachment MIME Type,Entity Refs,Entity Names\r\n"
        f"{log1.id},2024-01-01T00:00:00.000Z,Action Type 1,Action Category 1,,,,,,,,,,,,,entity,Entity\r\n"
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
                "source": [{"name": "source_field", "value": "source_value"}],
                "actor": {
                    "ref": "actor_ref",
                    "type": "actor",
                    "name": "Actor",
                    "extra": [{"name": "actor_field", "value": "actor_value"}],
                },
                "resource": {
                    "ref": "resource_ref",
                    "type": "resource",
                    "name": "Resource",
                    "extra": [{"name": "resource_field", "value": "resource_value"}],
                },
                "details": [{"name": "detail_field", "value": "detail_value"}],
            }
        ),
        saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z"),
    )
    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs/csv",
        params={
            "columns": "log_id,source.source_field,actor.actor_field,resource.resource_field,details.detail_field"
        },
    )
    assert (
        resp.text
        == "Log ID,Source: Source Field,Actor: Actor Field,Resource: Resource Field,Details: Detail Field\r\n"
        f"{log.id},source_value,actor_value,resource_value,detail_value\r\n"
    )
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"


async def test_get_logs_as_csv_custom_fields_enum(
    log_rw_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(
        log_rw_client,
        PreparedLog.prepare_data(
            {
                "source": [
                    {"name": "source_field", "value": "source_value", "type": "enum"}
                ],
                "actor": {
                    "ref": "actor_ref",
                    "type": "actor",
                    "name": "Actor",
                    "extra": [
                        {"name": "actor_field", "value": "actor_value", "type": "enum"}
                    ],
                },
                "resource": {
                    "ref": "resource_ref",
                    "type": "resource",
                    "name": "Resource",
                    "extra": [
                        {
                            "name": "resource_field",
                            "value": "resource_value",
                            "type": "enum",
                        }
                    ],
                },
                "details": [
                    {"name": "detail_field", "value": "detail_value", "type": "enum"}
                ],
            }
        ),
    )
    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs/csv",
        params={
            "columns": "log_id,source.source_field,actor.actor_field,resource.resource_field,details.detail_field",
        },
    )
    assert (
        resp.text
        == "Log ID,Source: Source Field,Actor: Actor Field,Resource: Resource Field,Details: Detail Field\r\n"
        f"{log.id},Source Value,Actor Value,Resource Value,Detail Value\r\n"
    )
    assert resp.headers["Content-Type"] == "text/csv; charset=utf-8"


async def test_get_logs_as_csv_boolean_fields(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(
        log_rw_client,
        PreparedLog.prepare_data(
            {
                "source": [{"name": "source_field", "value": True, "type": "boolean"}],
                "actor": {
                    "ref": "actor_ref",
                    "type": "actor",
                    "name": "Actor",
                    "extra": [
                        {"name": "actor_field", "value": True, "type": "boolean"}
                    ],
                },
                "resource": {
                    "ref": "resource_ref",
                    "type": "resource",
                    "name": "Resource",
                    "extra": [
                        {
                            "name": "resource_field",
                            "value": False,
                            "type": "boolean",
                        }
                    ],
                },
                "details": [
                    {"name": "detail_field", "value": False, "type": "boolean"}
                ],
            }
        ),
    )
    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs/csv",
        params={
            "columns": "log_id,source.source_field,actor.actor_field,resource.resource_field,details.detail_field",
        },
    )
    assert (
        resp.text
        == "Log ID,Source: Source Field,Actor: Actor Field,Resource: Resource Field,Details: Detail Field\r\n"
        f"{log.id},Yes,Yes,No,No\r\n"
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

    with patch("auditize.log.csv.get_config") as mock:
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
