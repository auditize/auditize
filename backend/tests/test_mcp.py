from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp.client import Client
from fastmcp.client.client import CallToolResult
from fastmcp.client.transports import FastMCPTransport
from fastmcp.exceptions import ToolError

from auditize.mcp.app import mcp
from conftest import ApikeyBuilder
from helpers.apikey import PreparedApikey
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


@pytest.fixture
async def mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client


@pytest.fixture
async def log_read_apikey(apikey_builder):
    return await apikey_builder({"logs": {"read": True}})


@contextmanager
def mock_mcp_http_headers(repo: PreparedRepo, apikey: PreparedApikey):
    with patch(
        "auditize.mcp.tools.get_http_headers",
        return_value={
            "x-auditize-repo": repo.id,
            "authorization": f"Bearer {apikey.key}",
        },
    ):
        yield


def _get_tool_data(result: CallToolResult) -> Any:
    return result.structured_content if result.structured_content else None


async def test_search_logs(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    log_1 = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    log_2 = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool(
            "search_logs", {"search_params": {"actor_ref": "2"}}
        )
    assert _get_tool_data(result) == {
        "items": [log_2.expected_api_response()],
        "next_cursor": None,
    }


async def test_search_logs_limited_permissions(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    log = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "read": True}]}}
    )

    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool("search_logs", {"search_params": {}})
    assert _get_tool_data(result) == {
        "items": [log.expected_api_response()],
        "next_cursor": None,
    }


async def test_search_logs_pagination(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    # emitted_at defaults to "now", so logs created later sort first (search_logs
    # orders by emitted_at desc)
    logs = [await repo.create_log_with(log_rw_client, {}) for _ in range(11)]
    logs.reverse()

    with mock_mcp_http_headers(repo, log_read_apikey):
        first_page = await mcp_client.call_tool("search_logs", {"search_params": {}})
    first_page_data = _get_tool_data(first_page)
    assert first_page_data["items"] == [
        log.expected_api_response() for log in logs[:10]
    ]
    assert first_page_data["next_cursor"] is not None

    with mock_mcp_http_headers(repo, log_read_apikey):
        second_page = await mcp_client.call_tool(
            "search_logs",
            {
                "search_params": {},
                "cursor": first_page_data["next_cursor"],
            },
        )
    second_page_data = _get_tool_data(second_page)
    assert second_page_data["items"] == [
        log.expected_api_response() for log in logs[10:]
    ]
    assert second_page_data["next_cursor"] is None


async def test_count_logs(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool(
            "count_logs", {"search_params": {"actor_ref": "2"}}
        )
    assert result.data == 1

    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("count_logs", {"search_params": {}})
    assert result.data == 2


async def test_search_actors(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("search_actors", {"query": "jane"})
    assert _get_tool_data(result) == {
        "items": [["Jane Doe", "2"]],
        "next_cursor": None,
    }


async def test_search_resources(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client,
        {"resource": {"type": "config", "ref": "cfg-1", "name": "Config Profile 123"}},
    )
    await repo.create_log_with(
        log_rw_client,
        {"resource": {"type": "doc", "ref": "doc-2", "name": "Document Template"}},
    )

    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("search_resources", {"query": "config"})
    assert _get_tool_data(result) == {
        "items": [["Config Profile 123", "cfg-1"]],
        "next_cursor": None,
    }


async def test_search_rich_tags(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "security"},
                {"type": "config", "name": "Config Profile 123", "ref": "cfg-1"},
            ]
        },
    )

    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("search_rich_tags", {"query": "prof"})
    assert _get_tool_data(result) == {
        "items": [["Config Profile 123", "cfg-1"]],
        "next_cursor": None,
    }


async def test_search_entities(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with_entity_path(log_rw_client, ["Customer", "Organization"])
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("search_entities", {"query": "orga"})
    assert _get_tool_data(result) == {
        "items": [
            {
                "ref": "Organization",
                "name": "Organization",
                "path": "Customer > Organization",
            }
        ],
        "next_cursor": None,
    }


async def test_list_action_types(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log(log_rw_client)
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_action_types")
    assert _get_tool_data(result) == {"items": ["user_login"], "next_cursor": None}


async def test_list_action_categories(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log(log_rw_client)
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_action_categories")
    assert _get_tool_data(result) == {
        "items": ["authentication"],
        "next_cursor": None,
    }


async def test_list_actor_types(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_actor_types")
    assert _get_tool_data(result) == {"items": ["user"], "next_cursor": None}


async def test_list_resource_types(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client,
        {"resource": {"type": "config", "ref": "cfg-1", "name": "Config Profile 123"}},
    )
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_resource_types")
    assert _get_tool_data(result) == {"items": ["config"], "next_cursor": None}


async def test_list_attachment_types(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(log_rw_client, type="text_file")
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_attachment_types")
    assert _get_tool_data(result) == {"items": ["text_file"], "next_cursor": None}


async def test_list_attachment_mime_types(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(log_rw_client, mime_type="text/plain")
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_attachment_mime_types")
    assert _get_tool_data(result) == {"items": ["text/plain"], "next_cursor": None}


async def test_list_simple_tag_types(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "security"},
                {"type": "config", "name": "Config Profile 123", "ref": "cfg-1"},
            ]
        },
    )
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_simple_tag_types")
    assert _get_tool_data(result) == {"items": ["security"], "next_cursor": None}


# One field per possible CustomFieldType (see auditize.log.models.CustomFieldType), sorted by
# name since that's the order the "fields" aggregation returns them in (composite agg, asc).
CUSTOM_FIELD_VALUES_BY_TYPE = [
    ("boolean_field", True, "boolean"),
    ("datetime_field", "2021-01-01T00:00:00.000Z", "datetime"),
    ("enum_field", "enum_value", "enum"),
    ("float_field", 123.45, "float"),
    ("integer_field", 123, "integer"),
    ("json_field", '{"foo": "bar"}', "json"),
    ("string_field", "string_value", "string"),
]

CUSTOM_FIELD_NAMES_AND_TYPES = [
    (name, field_type) for name, _, field_type in CUSTOM_FIELD_VALUES_BY_TYPE
]

CUSTOM_FIELDS_PAYLOAD = [
    {"name": name, "value": value, "type": field_type}
    for name, value, field_type in CUSTOM_FIELD_VALUES_BY_TYPE
]

EXPECTED_CUSTOM_FIELDS = [
    {"name": name, "type": field_type}
    for name, _, field_type in CUSTOM_FIELD_VALUES_BY_TYPE
]


@pytest.fixture
async def log_with_custom_fields(repo: PreparedRepo, log_rw_client: HttpTestHelper):
    return await repo.create_log_with(
        log_rw_client,
        {
            "source": CUSTOM_FIELDS_PAYLOAD,
            "actor": {
                "ref": "actor_ref",
                "type": "actor",
                "name": "Actor",
                "extra": CUSTOM_FIELDS_PAYLOAD,
            },
            "resource": {
                "ref": "resource_ref",
                "type": "resource",
                "name": "Resource",
                "extra": CUSTOM_FIELDS_PAYLOAD,
            },
            "details": CUSTOM_FIELDS_PAYLOAD,
        },
    )


@pytest.mark.usefixtures("log_with_custom_fields")
@pytest.mark.parametrize(
    "tool_name",
    [
        "list_source_fields",
        "list_details_fields",
        "list_actor_extra_fields",
        "list_resource_extra_fields",
    ],
)
async def test_list_custom_fields(
    tool_name: str,
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool(tool_name)
    assert _get_tool_data(result) == {
        "items": EXPECTED_CUSTOM_FIELDS,
        "next_cursor": None,
    }


@pytest.mark.usefixtures("log_with_custom_fields")
@pytest.mark.parametrize(
    "tool_name",
    [
        "list_source_field_values",
        "list_detail_field_values",
        "list_actor_extra_field_values",
        "list_resource_extra_field_values",
    ],
)
@pytest.mark.parametrize("field_name,field_type", CUSTOM_FIELD_NAMES_AND_TYPES)
async def test_list_custom_field_values(
    tool_name: str,
    field_name: str,
    field_type: str,
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool(tool_name, {"field_name": field_name})
    expected = ["enum_value"] if field_type == "enum" else []
    assert _get_tool_data(result) == {"items": expected, "next_cursor": None}


async def _aggregate_logs(
    mcp_client: Client[FastMCPTransport],
    repo: PreparedRepo,
    apikey: PreparedApikey,
    group_by: list[str],
    **params,
) -> dict:
    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool(
            "aggregate_logs", {"group_by": group_by, **params}
        )
    return _get_tool_data(result)


@pytest.mark.parametrize(
    "dimension,build_log_data",
    [
        (
            "action_type",
            lambda value: {"action": {"type": value, "category": "some_category"}},
        ),
        (
            "action_category",
            lambda value: {"action": {"type": "some_action", "category": value}},
        ),
        (
            "actor_type",
            lambda value: {"actor": {"type": value, "ref": "ref", "name": "Name"}},
        ),
        (
            "resource_type",
            lambda value: {"resource": {"type": value, "ref": "ref", "name": "Name"}},
        ),
    ],
)
async def test_aggregate_logs_scalar_dimensions(
    dimension: str,
    build_log_data,
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for value in ("value_b", "value_a", "value_b"):
        await repo.create_log_with(log_rw_client, build_log_data(value))

    assert await _aggregate_logs(mcp_client, repo, log_read_apikey, [dimension]) == {
        "total_count": 3,
        "rows": [
            {dimension: "value_b", "count": 2},
            {dimension: "value_a", "count": 1},
        ],
        "other_count": 0,
    }


@pytest.mark.parametrize("dimension", ["actor", "resource"])
async def test_aggregate_logs_by_actor_or_resource(
    dimension: str,
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for user_ref, name in (("1", "John Smith"), ("2", "Jane Doe"), ("1", "John Smith")):
        await repo.create_log_with(
            log_rw_client, {dimension: {"type": "user", "ref": user_ref, "name": name}}
        )

    assert await _aggregate_logs(mcp_client, repo, log_read_apikey, [dimension]) == {
        "total_count": 3,
        "rows": [
            {dimension: {"ref": "1", "name": "John Smith"}, "count": 2},
            {dimension: {"ref": "2", "name": "Jane Doe"}, "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_by_actor_uses_latest_name(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)

    # create the most recent log first to make sure the name does not depend
    # on the insertion order
    await repo.create_log_with(
        log_rw_client,
        {"actor": {"type": "user", "ref": "1", "name": "John Smith"}},
        emitted_at=now,
    )
    await repo.create_log_with(
        log_rw_client,
        {"actor": {"type": "user", "ref": "1", "name": "John"}},
        emitted_at=yesterday,
    )

    assert await _aggregate_logs(mcp_client, repo, log_read_apikey, ["actor"]) == {
        "total_count": 2,
        "rows": [
            {"actor": {"ref": "1", "name": "John Smith"}, "count": 2},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_two_dimensions(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for user_ref, action_type in (
        ("1", "login"),
        ("1", "login"),
        ("1", "login"),
        ("1", "logout"),
        ("2", "login"),
        ("2", "login"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                "action": {"type": action_type, "category": "authentication"},
                "actor": {"type": "user", "ref": user_ref, "name": f"User {user_ref}"},
            },
        )

    assert await _aggregate_logs(
        mcp_client, repo, log_read_apikey, ["actor", "action_type"]
    ) == {
        "total_count": 6,
        "rows": [
            {
                "actor": {"ref": "1", "name": "User 1"},
                "action_type": "login",
                "count": 3,
            },
            {
                "actor": {"ref": "2", "name": "User 2"},
                "action_type": "login",
                "count": 2,
            },
            {
                "actor": {"ref": "1", "name": "User 1"},
                "action_type": "logout",
                "count": 1,
            },
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_without_value(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "User 1"}}
    )
    await repo.create_log_with(log_rw_client, {})
    await repo.create_log_with(log_rw_client, {})

    # logs without actor are not part of any row but are counted in other_count
    assert await _aggregate_logs(mcp_client, repo, log_read_apikey, ["actor"]) == {
        "total_count": 3,
        "rows": [{"actor": {"ref": "1", "name": "User 1"}, "count": 1}],
        "other_count": 2,
    }


async def test_aggregate_logs_without_value_two_dimensions(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    actor = {"type": "user", "ref": "1", "name": "User 1"}
    resource = {"type": "config", "ref": "1", "name": "Resource 1"}
    for extra in (
        {"actor": actor, "resource": resource},
        {"actor": actor},
        {"actor": actor},
        {"resource": resource},
        {"resource": resource},
        {"resource": resource},
        {},
        {},
        {},
        {},
    ):
        await repo.create_log_with(log_rw_client, extra)

    assert await _aggregate_logs(
        mcp_client, repo, log_read_apikey, ["actor", "resource"]
    ) == {
        "total_count": 10,
        "rows": [
            {
                "actor": {"ref": "1", "name": "User 1"},
                "resource": {"ref": "1", "name": "Resource 1"},
                "count": 1,
            },
        ],
        "other_count": 9,
    }


async def test_aggregate_logs_limit_and_other_count(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for action_type, count in (("a", 5), ("b", 4), ("c", 3), ("d", 2), ("e", 1)):
        for _ in range(count):
            await repo.create_log_with(
                log_rw_client,
                {"action": {"type": action_type, "category": "authentication"}},
            )

    data = await _aggregate_logs(
        mcp_client, repo, log_read_apikey, ["action_type"], limit=2
    )
    assert data == {
        "total_count": 15,
        "rows": [
            {"action_type": "a", "count": 5},
            {"action_type": "b", "count": 4},
        ],
        "other_count": 6,
    }


async def test_aggregate_logs_tie_ordering(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    # Rows are sorted by count desc, then by key asc to break ties
    # ("b" is created before "a" to make sure insertion order is not used)
    for action_type in ("b", "a", "c", "c"):
        await repo.create_log_with(
            log_rw_client,
            {"action": {"type": action_type, "category": "authentication"}},
        )

    assert await _aggregate_logs(
        mcp_client, repo, log_read_apikey, ["action_type"]
    ) == {
        "total_count": 4,
        "rows": [
            {"action_type": "c", "count": 2},
            {"action_type": "a", "count": 1},
            {"action_type": "b", "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_empty(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    assert await _aggregate_logs(mcp_client, repo, log_read_apikey, ["actor"]) == {
        "total_count": 0,
        "rows": [],
        "other_count": 0,
    }


async def test_aggregate_logs_with_search_params(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for user_ref, status in (
        ("1", "failure"),
        ("1", "failure"),
        ("1", "success"),
        ("2", "failure"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                "actor": {"type": "user", "ref": user_ref, "name": f"User {user_ref}"},
                "details": [{"name": "status", "value": status, "type": "enum"}],
            },
        )

    assert await _aggregate_logs(
        mcp_client,
        repo,
        log_read_apikey,
        group_by=["actor"],
        search_params={"details": {"status": "failure"}},
    ) == {
        "total_count": 3,
        "rows": [
            {"actor": {"ref": "1", "name": "User 1"}, "count": 2},
            {"actor": {"ref": "2", "name": "User 2"}, "count": 1},
        ],
        "other_count": 0,
    }


def _build_log_data_with_custom_fields(prefix: str, fields: list[dict]) -> dict:
    match prefix:
        case "actor" | "resource":
            return {
                prefix: {"type": prefix, "ref": "1", "name": "Name", "extra": fields}
            }
        case _:
            return {prefix: fields}


@pytest.mark.parametrize("prefix", ["source", "details", "actor", "resource"])
@pytest.mark.parametrize(
    "field_type,values",
    [
        ("enum", ["a", "a", "b"]),
        ("boolean", [True, True, False]),
        ("integer", [200, 200, 404]),
        ("float", [1.5, 1.5, 2.5]),
    ],
)
async def test_aggregate_logs_by_custom_field(
    prefix: str,
    field_type: str,
    values: list,
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for value in values:
        await repo.create_log_with(
            log_rw_client,
            _build_log_data_with_custom_fields(
                prefix, [{"name": "field", "value": value, "type": field_type}]
            ),
        )
    # log without the custom field
    await repo.create_log_with(
        log_rw_client, _build_log_data_with_custom_fields(prefix, [])
    )

    dimension = f"{prefix}.field"
    assert await _aggregate_logs(mcp_client, repo, log_read_apikey, [dimension]) == {
        "total_count": 4,
        "rows": [
            {dimension: values[0], "count": 2},
            {dimension: values[2], "count": 1},
        ],
        "other_count": 1,
    }


async def test_aggregate_logs_by_two_non_keyword_custom_fields(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for success, code, duration in (
        (True, 200, 1.5),
        (True, 200, 1.5),
        (False, 404, 2.5),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                "details": [
                    {"name": "success", "value": success, "type": "boolean"},
                    {"name": "code", "value": code, "type": "integer"},
                    {"name": "duration", "value": duration, "type": "float"},
                ]
            },
        )

    assert await _aggregate_logs(
        mcp_client, repo, log_read_apikey, ["details.success", "details.code"]
    ) == {
        "total_count": 3,
        "rows": [
            {"details.success": True, "details.code": 200, "count": 2},
            {"details.success": False, "details.code": 404, "count": 1},
        ],
        "other_count": 0,
    }
    assert await _aggregate_logs(
        mcp_client, repo, log_read_apikey, ["details.duration", "details.success"]
    ) == {
        "total_count": 3,
        "rows": [
            {"details.duration": 1.5, "details.success": True, "count": 2},
            {"details.duration": 2.5, "details.success": False, "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_by_actor_and_actor_custom_field(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for user_ref, role in (("1", "admin"), ("1", "admin"), ("2", "user")):
        await repo.create_log_with(
            log_rw_client,
            {
                "actor": {
                    "type": "user",
                    "ref": user_ref,
                    "name": f"User {user_ref}",
                    "extra": [{"name": "role", "value": role, "type": "enum"}],
                }
            },
        )

    assert await _aggregate_logs(
        mcp_client, repo, log_read_apikey, ["actor", "actor.role"]
    ) == {
        "total_count": 3,
        "rows": [
            {
                "actor": {"ref": "1", "name": "User 1"},
                "actor.role": "admin",
                "count": 2,
            },
            {"actor": {"ref": "2", "name": "User 2"}, "actor.role": "user", "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_by_custom_field_with_search_params(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for action_type, status in (
        ("login", "failure"),
        ("login", "failure"),
        ("login", "success"),
        ("logout", "failure"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                "action": {"type": action_type, "category": "authentication"},
                "details": [{"name": "status", "value": status, "type": "enum"}],
            },
        )

    assert await _aggregate_logs(
        mcp_client,
        repo,
        log_read_apikey,
        ["action_type", "details.status"],
        search_params={"action_type": "login"},
    ) == {
        "total_count": 3,
        "rows": [
            {"action_type": "login", "details.status": "failure", "count": 2},
            {"action_type": "login", "details.status": "success", "count": 1},
        ],
        "other_count": 0,
    }


@pytest.mark.parametrize("field_type", ["string", "json", "datetime"])
async def test_aggregate_logs_by_custom_field_unsupported_type(
    field_type: str,
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_with_custom_fields,
    mcp_client: Client[FastMCPTransport],
):
    with pytest.raises(ToolError, match="cannot be used as dimension"):
        await _aggregate_logs(
            mcp_client, repo, log_read_apikey, [f"details.{field_type}_field"]
        )


async def test_aggregate_logs_by_unknown_custom_field(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_with_custom_fields,
    mcp_client: Client[FastMCPTransport],
):
    with pytest.raises(ToolError, match="Unknown custom field"):
        await _aggregate_logs(mcp_client, repo, log_read_apikey, ["details.unknown"])


@pytest.mark.parametrize(
    "group_by",
    [
        ["unknown_prefix.enum_field"],
        ["details."],
        ["details.enum_field", "details.enum_field"],
    ],
)
async def test_aggregate_logs_by_custom_field_invalid_group_by(
    group_by: list[str],
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_with_custom_fields,
    mcp_client: Client[FastMCPTransport],
):
    with pytest.raises(ToolError):
        await _aggregate_logs(mcp_client, repo, log_read_apikey, group_by)


async def test_aggregate_logs_limited_permissions(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client, {"action": {"type": "login", "category": "authentication"}}
    )
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "read": True}]}}
    )

    assert await _aggregate_logs(mcp_client, repo, apikey, ["action_type"]) == {
        "total_count": 1,
        "rows": [{"action_type": "login", "count": 1}],
        "other_count": 0,
    }


async def test_aggregate_logs_entity_restricted(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with_entity_path(log_rw_client, ["entity_A"])
    await repo.create_log_with_entity_path(log_rw_client, ["entity_A", "entity_A1"])
    await repo.create_log_with_entity_path(log_rw_client, ["entity_B"])
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "readable_entities": ["entity_A"]}]}}
    )

    assert await _aggregate_logs(mcp_client, repo, apikey, ["action_type"]) == {
        "total_count": 2,
        "rows": [{"action_type": "user_login", "count": 2}],
        "other_count": 0,
    }


async def test_aggregate_logs_no_permission(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    mcp_client: Client[FastMCPTransport],
):
    apikey = await apikey_builder({})
    with pytest.raises(ToolError, match="permission"):
        await _aggregate_logs(mcp_client, repo, apikey, ["action_type"])


async def test_aggregate_logs_invalid_group_by(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    with pytest.raises(ToolError):
        await _aggregate_logs(mcp_client, repo, log_read_apikey, ["unknown_dimension"])


async def test_aggregate_logs_invalid_limit(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    with pytest.raises(ToolError):
        await _aggregate_logs(
            mcp_client, repo, log_read_apikey, ["action_type"], limit=51
        )


async def _aggregate_logs_over_time(
    mcp_client: Client[FastMCPTransport],
    repo: PreparedRepo,
    apikey: PreparedApikey,
    interval: str,
    **params,
) -> dict:
    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool(
            "aggregate_logs_over_time", {"interval": interval, **params}
        )
    return _get_tool_data(result)


def _actor(ref: str) -> dict:
    return {"actor": {"type": "user", "ref": ref, "name": f"User {ref}"}}


def _empty_cyclic_timeline(periods, **extra) -> list[dict]:
    return [{"period": period, "count": 0, **extra} for period in periods]


async def test_aggregate_logs_over_time_histogram(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for emitted_at in (
        "2026-01-15T08:30:00Z",  # outside the time window
        "2026-01-15T10:05:00Z",
        "2026-01-15T10:20:00Z",
        "2026-01-15T12:30:00Z",
        "2026-01-15T13:30:00Z",  # outside the time window
    ):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    assert await _aggregate_logs_over_time(
        mcp_client,
        repo,
        log_read_apikey,
        "1_hour",
        search_params={
            "since": "2026-01-15T09:00:00Z",
            "until": "2026-01-15T12:59:59Z",
        },
    ) == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T09:00:00Z",
        "end": "2026-01-15T12:59:59Z",
        "total_count": 3,
        "timeline": [
            {"period": "2026-01-15T09:00:00Z", "count": 0},
            {"period": "2026-01-15T10:00:00Z", "count": 2},
            {"period": "2026-01-15T11:00:00Z", "count": 0},
            {"period": "2026-01-15T12:00:00Z", "count": 1},
        ],
    }


async def test_aggregate_logs_over_time_window_from_logs(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for emitted_at in ("2026-01-15T10:05:00Z", "2026-01-15T12:30:00Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    assert await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "1_hour"
    ) == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T10:05:00Z",
        "end": "2026-01-15T12:30:00Z",
        "total_count": 2,
        "timeline": [
            {"period": "2026-01-15T10:00:00Z", "count": 1},
            {"period": "2026-01-15T11:00:00Z", "count": 0},
            {"period": "2026-01-15T12:00:00Z", "count": 1},
        ],
    }

    # only "since" is given, "until" is the date of the most recent log
    data = await _aggregate_logs_over_time(
        mcp_client,
        repo,
        log_read_apikey,
        "1_hour",
        search_params={"since": "2026-01-15T11:00:00Z"},
    )
    assert data["start"] == "2026-01-15T11:00:00Z"
    assert data["end"] == "2026-01-15T12:30:00Z"
    assert data["timeline"] == [
        {"period": "2026-01-15T11:00:00Z", "count": 0},
        {"period": "2026-01-15T12:00:00Z", "count": 1},
    ]


async def test_aggregate_logs_over_time_empty(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    assert await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "1_hour", split_by="actor"
    ) == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": None,
        "end": None,
        "total_count": 0,
        "timeline": [],
    }

    assert await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "day_of_week", split_by="actor"
    ) == {
        "interval": "day_of_week",
        "timezone": "UTC",
        "start": None,
        "end": None,
        "total_count": 0,
        "timeline": _empty_cyclic_timeline(
            [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ],
            breakdown=[],
            other_count=0,
        ),
    }


async def test_aggregate_logs_over_time_empty_with_time_window(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    data = await _aggregate_logs_over_time(
        mcp_client,
        repo,
        log_read_apikey,
        "1_day",
        search_params={
            "since": "2026-01-15T00:00:00Z",
            "until": "2026-01-16T23:59:59Z",
        },
        count_distinct="actor",
    )
    assert data["total_count"] == 0
    assert data["timeline"] == [
        {"period": "2026-01-15T00:00:00Z", "count": 0, "distinct_count": 0},
        {"period": "2026-01-16T00:00:00Z", "count": 0, "distinct_count": 0},
    ]


async def test_aggregate_logs_over_time_daily_with_timezone(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    # 2026-01-15 23:30 and 2026-01-16 00:30 in Europe/Paris (UTC+1)
    for emitted_at in ("2026-01-15T22:30:00Z", "2026-01-15T23:30:00Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    assert await _aggregate_logs_over_time(
        mcp_client,
        repo,
        log_read_apikey,
        "1_day",
        timezone="Europe/Paris",
        search_params={
            "since": "2026-01-14T23:00:00Z",
            "until": "2026-01-16T22:59:59Z",
        },
    ) == {
        "interval": "1_day",
        "timezone": "Europe/Paris",
        "start": "2026-01-15T00:00:00+01:00",
        "end": "2026-01-16T23:59:59+01:00",
        "total_count": 2,
        "timeline": [
            {"period": "2026-01-15T00:00:00+01:00", "count": 1},
            {"period": "2026-01-16T00:00:00+01:00", "count": 1},
        ],
    }


async def test_aggregate_logs_over_time_hour_of_day(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for emitted_at in (
        "2026-01-15T02:10:00Z",  # 03:10 in Europe/Paris
        "2026-01-16T02:50:00Z",  # 03:50 in Europe/Paris
        "2026-01-17T13:00:00Z",  # 14:00 in Europe/Paris
    ):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    data = await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "hour_of_day", timezone="Europe/Paris"
    )
    expected_timeline = _empty_cyclic_timeline(range(24))
    expected_timeline[3]["count"] = 2
    expected_timeline[14]["count"] = 1
    assert data == {
        "interval": "hour_of_day",
        "timezone": "Europe/Paris",
        "start": "2026-01-15T03:10:00+01:00",
        "end": "2026-01-17T14:00:00+01:00",
        "total_count": 3,
        "timeline": expected_timeline,
    }


async def test_aggregate_logs_over_time_hour_of_day_across_dst_change(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    # Europe/Paris switches from UTC+1 to UTC+2 on 2026-03-29
    for emitted_at in ("2026-03-28T08:00:00Z", "2026-03-30T07:00:00Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    data = await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "hour_of_day", timezone="Europe/Paris"
    )
    expected_timeline = _empty_cyclic_timeline(range(24))
    expected_timeline[9]["count"] = 2
    assert data["timeline"] == expected_timeline


async def test_aggregate_logs_over_time_day_of_week(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for emitted_at in (
        "2026-01-12T10:00:00Z",  # monday
        "2026-01-17T23:30:00Z",  # saturday in UTC, sunday in Europe/Paris
        "2026-01-19T10:00:00Z",  # monday
    ):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    data = await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "day_of_week", timezone="Europe/Paris"
    )
    assert data["total_count"] == 3
    assert data["timeline"] == [
        {"period": "monday", "count": 2},
        {"period": "tuesday", "count": 0},
        {"period": "wednesday", "count": 0},
        {"period": "thursday", "count": 0},
        {"period": "friday", "count": 0},
        {"period": "saturday", "count": 0},
        {"period": "sunday", "count": 1},
    ]


async def test_aggregate_logs_over_time_split_by_actor(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    # top 2 actors over the time window are 1 (3 logs) and 2 (2 logs), actor 3
    # is not part of the top even if it is as active as actor 1 at 12:00
    for emitted_at, extra in (
        ("2026-01-15T10:05:00Z", _actor("1")),
        ("2026-01-15T10:10:00Z", _actor("1")),
        ("2026-01-15T10:20:00Z", _actor("2")),
        ("2026-01-15T11:05:00Z", _actor("2")),
        ("2026-01-15T11:10:00Z", {}),
        ("2026-01-15T12:05:00Z", _actor("1")),
        ("2026-01-15T12:10:00Z", _actor("3")),
    ):
        await repo.create_log_with(log_rw_client, extra, emitted_at=emitted_at)

    data = await _aggregate_logs_over_time(
        mcp_client,
        repo,
        log_read_apikey,
        "1_hour",
        split_by="actor",
        split_limit=2,
    )
    assert data["total_count"] == 7
    assert data["timeline"] == [
        {
            "period": "2026-01-15T10:00:00Z",
            "count": 3,
            "breakdown": [
                {"actor": {"ref": "1", "name": "User 1"}, "count": 2},
                {"actor": {"ref": "2", "name": "User 2"}, "count": 1},
            ],
            "other_count": 0,
        },
        {
            "period": "2026-01-15T11:00:00Z",
            "count": 2,
            "breakdown": [{"actor": {"ref": "2", "name": "User 2"}, "count": 1}],
            "other_count": 1,
        },
        {
            "period": "2026-01-15T12:00:00Z",
            "count": 2,
            "breakdown": [{"actor": {"ref": "1", "name": "User 1"}, "count": 1}],
            "other_count": 1,
        },
    ]


async def test_aggregate_logs_over_time_split_by_custom_field_cyclic(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for emitted_at, status in (
        ("2026-01-15T02:00:00Z", "failure"),
        ("2026-01-16T02:30:00Z", "failure"),
        ("2026-01-16T14:00:00Z", "success"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {"details": [{"name": "status", "value": status, "type": "enum"}]},
            emitted_at=emitted_at,
        )

    data = await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "hour_of_day", split_by="details.status"
    )
    expected_timeline = _empty_cyclic_timeline(range(24), breakdown=[], other_count=0)
    expected_timeline[2] = {
        "period": 2,
        "count": 2,
        "breakdown": [{"details.status": "failure", "count": 2}],
        "other_count": 0,
    }
    expected_timeline[14] = {
        "period": 14,
        "count": 1,
        "breakdown": [{"details.status": "success", "count": 1}],
        "other_count": 0,
    }
    assert data["timeline"] == expected_timeline


async def test_aggregate_logs_over_time_count_distinct(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for emitted_at, actor_ref, action_type in (
        ("2026-01-15T10:05:00Z", "1", "login"),
        ("2026-01-15T10:10:00Z", "2", "login"),
        ("2026-01-15T10:20:00Z", "1", "login"),
        ("2026-01-15T10:30:00Z", "1", "logout"),
        ("2026-01-15T11:30:00Z", "3", "login"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                **_actor(actor_ref),
                "action": {"type": action_type, "category": "authentication"},
            },
            emitted_at=emitted_at,
        )

    data = await _aggregate_logs_over_time(
        mcp_client,
        repo,
        log_read_apikey,
        "1_hour",
        split_by="action_type",
        count_distinct="actor",
    )
    assert data["timeline"] == [
        {
            "period": "2026-01-15T10:00:00Z",
            "count": 4,
            "distinct_count": 2,
            "breakdown": [
                {"action_type": "login", "count": 3, "distinct_count": 2},
                {"action_type": "logout", "count": 1, "distinct_count": 1},
            ],
            "other_count": 0,
        },
        {
            "period": "2026-01-15T11:00:00Z",
            "count": 1,
            "distinct_count": 1,
            "breakdown": [{"action_type": "login", "count": 1, "distinct_count": 1}],
            "other_count": 0,
        },
    ]


async def test_aggregate_logs_over_time_with_search_params(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for emitted_at, action_type in (
        ("2026-01-15T10:05:00Z", "login"),
        ("2026-01-15T10:10:00Z", "logout"),
        ("2026-01-15T11:05:00Z", "login"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {"action": {"type": action_type, "category": "authentication"}},
            emitted_at=emitted_at,
        )

    data = await _aggregate_logs_over_time(
        mcp_client,
        repo,
        log_read_apikey,
        "1_hour",
        search_params={"action_type": "login"},
    )
    assert data["total_count"] == 2
    assert data["timeline"] == [
        {"period": "2026-01-15T10:00:00Z", "count": 1},
        {"period": "2026-01-15T11:00:00Z", "count": 1},
    ]


async def test_aggregate_logs_over_time_too_many_periods(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    one_day = {"since": "2026-01-15T00:00:00Z", "until": "2026-01-15T23:59:59Z"}
    with pytest.raises(ToolError, match="Too many periods.*'15_minutes'"):
        await _aggregate_logs_over_time(
            mcp_client, repo, log_read_apikey, "5_minutes", search_params=one_day
        )

    # the limit is lower when split_by is used
    half_a_day = {"since": "2026-01-15T00:00:00Z", "until": "2026-01-15T11:59:59Z"}
    await _aggregate_logs_over_time(
        mcp_client, repo, log_read_apikey, "5_minutes", search_params=half_a_day
    )
    with pytest.raises(ToolError, match="Too many periods.*with split_by"):
        await _aggregate_logs_over_time(
            mcp_client,
            repo,
            log_read_apikey,
            "5_minutes",
            search_params=half_a_day,
            split_by="actor",
        )


async def test_aggregate_logs_over_time_cyclic_time_window_too_large(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    with pytest.raises(ToolError, match="Time window is too large"):
        await _aggregate_logs_over_time(
            mcp_client,
            repo,
            log_read_apikey,
            "hour_of_day",
            search_params={
                "since": "2020-01-01T00:00:00Z",
                "until": "2023-01-01T00:00:00Z",
            },
        )


@pytest.mark.parametrize(
    "params,error",
    [
        ({"interval": "2h"}, None),
        ({"interval": "1_hour", "timezone": "Mars/Olympus"}, "Invalid timezone"),
        ({"interval": "1_hour", "split_by": "unknown"}, "Invalid dimension"),
        ({"interval": "1_hour", "count_distinct": "unknown"}, "Invalid dimension"),
        (
            {"interval": "1_hour", "split_by": "actor", "count_distinct": "actor"},
            "must be different",
        ),
        (
            {"interval": "hour_of_day", "count_distinct": "actor"},
            "count_distinct cannot be used",
        ),
        ({"interval": "1_hour", "split_by": "actor", "split_limit": 11}, None),
        (
            {
                "interval": "1_hour",
                "search_params": {
                    "since": "2026-01-16T00:00:00Z",
                    "until": "2026-01-15T00:00:00Z",
                },
            },
            "since must be before until",
        ),
    ],
)
async def test_aggregate_logs_over_time_invalid_params(
    params: dict,
    error: str | None,
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
):
    with pytest.raises(ToolError, match=error):
        await _aggregate_logs_over_time(mcp_client, repo, log_read_apikey, **params)


async def test_aggregate_logs_over_time_entity_restricted(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with_entity_path(log_rw_client, ["entity_A"])
    await repo.create_log_with_entity_path(log_rw_client, ["entity_A", "entity_A1"])
    await repo.create_log_with_entity_path(log_rw_client, ["entity_B"])
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "readable_entities": ["entity_A"]}]}}
    )

    data = await _aggregate_logs_over_time(mcp_client, repo, apikey, "day_of_week")
    assert data["total_count"] == 2
    assert sum(period["count"] for period in data["timeline"]) == 2


async def test_aggregate_logs_over_time_no_permission(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    mcp_client: Client[FastMCPTransport],
):
    apikey = await apikey_builder({})
    with pytest.raises(ToolError, match="permission"):
        await _aggregate_logs_over_time(mcp_client, repo, apikey, "1_hour")
