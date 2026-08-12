import logging

from fastmcp import FastMCP
from fastmcp.server.middleware.logging import LoggingMiddleware

logging.basicConfig(level=logging.INFO)


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
