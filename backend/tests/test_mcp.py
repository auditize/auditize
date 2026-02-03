from contextlib import contextmanager
from unittest.mock import patch

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport

from auditize.mcp import mcp
from helpers.apikey import PreparedApikey
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


@pytest.fixture
async def mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client


@contextmanager
def mock_mcp_http_headers(repo: PreparedRepo, apikey: PreparedApikey):
    with patch(
        "auditize.mcp.get_http_headers",
        return_value={
            "x-auditize-repo": repo.id,
            "Authorization": f"Bearer {apikey.key}",
        },
    ):
        yield


async def test_search_logs(
    repo: PreparedRepo,
    apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    log_1 = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    log_2 = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool(
            "search_logs", {"search_params": {"actor_ref": "2"}}
        )
    assert result.data == [log_2.expected_api_response()]


async def test_search_actors(
    repo: PreparedRepo,
    apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool("search_actors", {"query": "jane"})
    assert result.data == [["Jane Doe", "2"]]


async def test_search_resources(
    repo: PreparedRepo,
    apikey: PreparedApikey,
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

    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool("search_resources", {"query": "config"})
    assert result.data == [["Config Profile 123", "cfg-1"]]


async def test_search_entities(
    repo: PreparedRepo,
    apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with_entity_path(log_rw_client, ["Customer", "Organization"])
    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool("search_entities", {"query": "orga"})
    assert result.data == [
        {
            "ref": "Organization",
            "name": "Organization",
            "path": "Customer > Organization",
        }
    ]


async def test_list_action_types(
    repo: PreparedRepo,
    apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log(log_rw_client)
    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool("list_action_types")
    assert result.data == ["user_login"]


async def test_list_action_categories(
    repo: PreparedRepo,
    apikey: PreparedApikey,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log(log_rw_client)
    with mock_mcp_http_headers(repo, apikey):
        result = await mcp_client.call_tool("list_action_categories")
    assert result.data == ["authentication"]
