from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware
from fastmcp.utilities.logging import configure_logging

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
