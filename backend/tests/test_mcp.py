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
def mock_mcp_http_headers(headers: dict):
    with patch("auditize.mcp.get_http_headers", return_value=headers):
        yield


async def test_list_tools(mcp_client: Client[FastMCPTransport]):
    list_tools = await mcp_client.list_tools()

    print(len(list_tools))

    assert len(list_tools) != 0


async def test_search_entities(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    apikey = await PreparedApikey.inject_into_db()
    await repo.create_log_with_entity_path(log_rw_client, ["Customer", "Organization"])
    with mock_mcp_http_headers(
        {"x-auditize-repo": repo.id, "Authorization": f"Bearer {apikey.key}"}
    ):
        result = await mcp_client.call_tool("search_entities", {"query": "orga"})
    assert result.data == [
        {
            "ref": "Organization",
            "name": "Organization",
            "path": "Customer > Organization",
        }
    ]
