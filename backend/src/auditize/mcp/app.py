from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.utilities.logging import configure_logging

from auditize.llm_tools.tools import LOG_TOOLS
from auditize.mcp.tool_adapter import to_mcp_tool

configure_logging(level="INFO")


mcp = FastMCP(
    "Auditize MCP Connector",
    "Provides Auditize log exploring capabilities for a given repository",
)

mcp.add_middleware(
    LoggingMiddleware(
        include_payloads=True,
        include_payload_length=True,
    )
)

for tool in LOG_TOOLS:
    mcp.add_tool(to_mcp_tool(tool))
