from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp.client import Client
from fastmcp.client.client import CallToolResult
from fastmcp.client.transports import FastMCPTransport

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
