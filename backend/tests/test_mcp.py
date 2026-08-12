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
    return result.structured_content["result"] if result.structured_content else None


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
    assert _get_tool_data(result) == [log_2.expected_api_response()]


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
    assert _get_tool_data(result) == [log.expected_api_response()]


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
    assert _get_tool_data(result) == [["Jane Doe", "2"]]


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
    assert _get_tool_data(result) == [["Config Profile 123", "cfg-1"]]


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
    assert _get_tool_data(result) == [["Config Profile 123", "cfg-1"]]


async def test_search_entities(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with_entity_path(log_rw_client, ["Customer", "Organization"])
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("search_entities", {"query": "orga"})
    assert _get_tool_data(result) == [
        {
            "ref": "Organization",
            "name": "Organization",
            "path": "Customer > Organization",
        }
    ]


async def test_list_action_types(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log(log_rw_client)
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_action_types")
    assert _get_tool_data(result) == ["user_login"]


async def test_list_action_categories(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log(log_rw_client)
    with mock_mcp_http_headers(repo, log_read_apikey):
        result = await mcp_client.call_tool("list_action_categories")
    assert _get_tool_data(result) == ["authentication"]
