import logging
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.dependencies import Depends
from fastmcp.server.dependencies import get_http_headers
from fastmcp.server.middleware.logging import LoggingMiddleware
from mcp.types import ToolAnnotations
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database.dbm import open_db_session
from auditize.log.models import LogEntityMcpResponse, LogResponse, LogSearchParams
from auditize.log.service import LogService

logging.basicConfig(level=logging.INFO)

mcp = FastMCP(
    "Auditize MCP Connector",
    "Provides Auditize log exploring capabilities for a given repository",
    log_level="INFO",
)

mcp.add_middleware(
    LoggingMiddleware(
        include_payloads=True,
        include_payload_length=True,
    )
)


async def get_log_service(db_session: AsyncSession) -> LogService:
    headers = get_http_headers()
    repo_id = headers.get("x-auditize-repo")
    if not repo_id:
        raise ValueError("X-Auditize-Repo header is required")
    return await LogService.for_reading(db_session, repo_id)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=False,  # Only internal data
    )
)
async def search_logs(
    search_params: LogSearchParams,
    db_session: AsyncSession = Depends(open_db_session),
) -> list[LogResponse]:
    """Search for logs in the repository given optional keywords in the query. Return at most 10 logs."""
    log_service = await get_log_service(db_session)
    logs, _ = await log_service.get_logs(search_params=search_params)
    return [LogResponse.model_validate(log.model_dump()) for log in logs]


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=False,  # Only internal data
    )
)
async def search_actors(
    query: Annotated[str | None, "The query (keywords) to search for actors"],
    db_session: AsyncSession = Depends(open_db_session),
) -> list[tuple[str, str]]:
    """Search for actors on partial name match ("Jo Do" will match "John Doe").

    Returns a list of tuples (actor_name, actor_ref) for matching actors.

    IMPORTANT: When searching for logs, use the actor_ref (second element of each tuple)
    with search_logs(actor_ref=...) rather than actor_name. The actor_ref is the unique
    identifier and provides more accurate filtering than actor_name.

    Example workflow:
    1. Call search_actors(query="John") to find actors
    2. Use the actor_ref from the results: search_logs(actor_ref="user:123")

    At most 10 results are returned."""
    log_service = await get_log_service(db_session)
    actors, _ = await log_service.get_log_actor_names(search=query)
    return actors


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=False,  # Only internal data
    )
)
async def search_entities(
    query: Annotated[str, "The query (keywords) to search for entities"],
    db_session: AsyncSession = Depends(open_db_session),
) -> list[LogEntityMcpResponse]:
    """Search for entities on partial name match ("Ent" will match "Entity 1").

    Returns a list of LogEntityMcpResponse for matching entities.

    When searching for logs on a specific entity:
    - first: call search_entities to get the list of possible entities
    - then: use the ref of the entity with search_logs(entity_ref=ref)

    At most 10 results are returned."""
    log_service = await get_log_service(db_session)
    entities, _ = await log_service.get_log_entities(
        search=query, authorized_entities=set()
    )

    return [
        LogEntityMcpResponse(
            ref=entity.ref,
            name=entity.name,
            path=" > ".join(
                [ent.name async for ent in log_service.iter_on_log_entity_path(entity)]
            ),
        )
        for entity in entities
    ]


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=False,  # Only internal data
    )
)
async def list_action_types(
    db_session: AsyncSession = Depends(open_db_session),
) -> list[str]:
    """List all possible action types.

    When searching for logs on a specific action type:
    - first: call list_action_types to get the list of possible action types
    - then: use the action_type with search_logs(action_type=...)
    """
    log_service = await get_log_service(db_session)
    action_types, _ = await log_service.get_log_action_types(
        limit=100, pagination_cursor=None
    )
    return action_types


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True,
        openWorldHint=False,  # Only internal data
    )
)
async def list_action_categories(
    db_session: AsyncSession = Depends(open_db_session),
) -> list[str]:
    """List all possible action categories (action categories are used to group action types).

    When searching for logs on a specific action category:
    - first: call list_action_categories to get the list of possible action categories
    - then: use the action_category with search_logs(action_category=...)
    """
    log_service = await get_log_service(db_session)
    action_categories, _ = await log_service.get_log_action_categories(
        limit=100, pagination_cursor=None
    )
    return action_categories
