import uuid
from typing import Annotated

from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from mcp.types import ToolAnnotations
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.auth.authorizer import (
    Authenticated,
    authenticate_apikey,
    get_bearer_token_from_authorization_header,
)
from auditize.database.dbm import open_db_session
from auditize.log.models import LogEntityMcpResponse, LogResponse, LogSearchParams
from auditize.log.service import LogService
from auditize.mcp.app import mcp
from auditize.permissions.assertions import can_read_logs_from_repo

TOOL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,  # Only internal data
)

TOOL_MAX_RESULTS = 20


async def get_authorized(
    db_session: AsyncSession = Depends(open_db_session),
) -> Authenticated:
    headers = get_http_headers(include_all=True)

    authorization_header = headers.get("authorization")
    if not authorization_header:
        raise ToolError(f"Authorization header is required (actual headers: {headers})")

    bearer_token = get_bearer_token_from_authorization_header(authorization_header)
    authenticated = await authenticate_apikey(db_session, bearer_token)

    return authenticated


async def get_log_service(
    db_session: AsyncSession = Depends(open_db_session),
    authenticated: Authenticated = Depends(get_authorized),
) -> LogService:
    headers = get_http_headers()

    raw_repo_id = headers.get("x-auditize-repo")
    if not raw_repo_id:
        raise ToolError("X-Auditize-Repo header is required")

    try:
        repo_id = uuid.UUID(raw_repo_id)
    except ValueError:
        raise ToolError(f"Invalid X-Auditize-Repo header {raw_repo_id!r}")

    if not authenticated.comply(can_read_logs_from_repo(repo_id)):
        raise ToolError(
            f"Apikey does not have permission to read logs from repository {repo_id!r}"
        )

    return await LogService.for_reading(db_session, repo_id)


def get_authorized_entities(
    log_service: LogService = Depends(get_log_service),
    authorized: Authenticated = Depends(get_authorized),
) -> set[str]:
    return authorized.permissions.get_repo_readable_entities(log_service.repo.id)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_logs(
    search_params: LogSearchParams,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> list[LogResponse]:
    """Search for logs in the repository given optional keywords in the query. Return at most 10 logs."""
    logs, _ = await log_service.get_logs(
        search_params=search_params, authorized_entities=authorized_entities
    )
    return [LogResponse.model_validate(log.model_dump()) for log in logs]


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_actors(
    query: Annotated[str | None, "The query (keywords) to search for actors"],
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
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
    actors, _ = await log_service.get_log_actor_names(
        search=query, authorized_entities=authorized_entities
    )
    return actors


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_resources(
    query: Annotated[str | None, "The query (keywords) to search for resources"],
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> list[tuple[str, str]]:
    """Search for resources on partial name match ("Config" will match "Config Profile 123").

    Returns a list of tuples (resource_name, resource_ref) for matching resources.

    IMPORTANT: When searching for logs, use the resource_ref (second element of each tuple)
    with search_logs(resource_ref=...) rather than resource_name. The resource_ref is the unique
    identifier and provides more accurate filtering than resource_name.

    Example workflow:
    1. Call search_resources(query="Config") to find resources
    2. Use the resource_ref from the results: search_logs(resource_ref="config:123")

    At most 10 results are returned."""
    resources, _ = await log_service.get_log_resource_names(
        search=query, authorized_entities=authorized_entities
    )
    return resources


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_rich_tags(
    query: Annotated[str | None, "The query (keywords) to search for rich tags"],
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> list[tuple[str, str]]:
    """Search for rich tags on partial name match ("abc" will match "Profile ABC").

    Rich tags are tags that tracks a resource accross logs.

    Returns a list of tuples (tag_name, tag_ref) for matching tags.

    IMPORTANT: When searching for logs, use the tag_ref (second element of each tuple)
    with search_logs(tag_ref=...) rather than tag_name. The tag_ref is the unique
    identifier and provides more accurate filtering than tag_name.

    Example workflow:
    1. Call search_tags(query="abc") to find tags
    2. Use the tag_ref from the results: search_logs(tag_ref="profile:abc")

    At most 10 results are returned."""
    tags, _ = await log_service.get_log_tag_names(
        search=query, authorized_entities=authorized_entities
    )
    return tags


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_entities(
    query: Annotated[str, "The query (keywords) to search for entities"],
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> list[LogEntityMcpResponse]:
    """Search for entities on partial name match ("Ent" will match "Entity 1").

    Returns a list of LogEntityMcpResponse for matching entities.

    When searching for logs on a specific entity:
    - first: call search_entities to get the list of possible entities
    - then: use the ref of the entity with search_logs(entity_ref=ref)

    At most 10 results are returned."""
    entities, _ = await log_service.get_log_entities(
        search=query, authorized_entities=authorized_entities
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


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_action_types(
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> list[str]:
    """List all possible action types.

    When searching for logs on a specific action type:
    - first: call list_action_types to get the list of possible action types
    - then: use the action_type with search_logs(action_type=...)
    """
    action_types, _ = await log_service.get_log_action_types(
        limit=100, pagination_cursor=None, authorized_entities=authorized_entities
    )
    return action_types


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_action_categories(
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> list[str]:
    """List all possible action categories (action categories are used to group action types).

    When searching for logs on a specific action category:
    - first: call list_action_categories to get the list of possible action categories
    - then: use the action_category with search_logs(action_category=...)
    """
    action_categories, _ = await log_service.get_log_action_categories(
        limit=100, pagination_cursor=None, authorized_entities=authorized_entities
    )
    return action_categories
