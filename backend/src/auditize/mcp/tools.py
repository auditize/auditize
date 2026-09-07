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
from auditize.log.models import (
    CustomFieldData,
    LogResponse,
    LogSearchParams,
)
from auditize.log.service import LogService
from auditize.mcp.app import mcp
from auditize.mcp.models import LogEntityMcpResponse, PaginatedMcpResponse
from auditize.permissions.assertions import can_read_logs_from_repo

TOOL_ANNOTATIONS = ToolAnnotations(
    readOnlyHint=True,
    openWorldHint=False,  # Only internal data
)

# Page size used by all tools, except search_logs which returns heavier objects.
DEFAULT_TOOL_PAGE_LIMIT = 50
SEARCH_LOGS_PAGE_LIMIT = 10

CURSOR_PARAM_DESCRIPTION = (
    "Pagination cursor from a previous call's next_cursor field. "
    "Leave unset to get the first page."
)


async def get_authorized(
    db_session: AsyncSession = Depends(open_db_session),
) -> Authenticated:
    headers = get_http_headers(include_all=True)

    authorization_header = headers.get("authorization")
    if not authorization_header:
        raise ToolError(f"Authorization header is required")

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
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[LogResponse]:
    """Search for logs in the repository given optional keywords in the query.

    Results are paginated (10 logs per page). If the response's `next_cursor` is not
    null, call this tool again with the same search_params and `cursor` set to that
    value to fetch the next page.

    To filter on custom fields (source, details, actor_extra, resource_extra), first discover
    available field names and their type with list_source_fields / list_details_fields /
    list_actor_extra_fields / list_resource_extra_fields, then for fields of type "enum" get
    their possible values with the matching list_source_field_values / list_detail_field_values /
    list_actor_extra_field_values / list_resource_extra_field_values tool.
    """
    logs, next_cursor = await log_service.get_logs(
        search_params=search_params,
        authorized_entities=authorized_entities,
        limit=SEARCH_LOGS_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedMcpResponse(
        items=[LogResponse.model_validate(log.model_dump()) for log in logs],
        next_cursor=next_cursor,
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_actors(
    query: Annotated[str | None, "The query (keywords) to search for actors"],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[tuple[str, str]]:
    """Search for actors on partial name match ("Jo Do" will match "John Doe").

    Returns a paginated list of tuples (actor_name, actor_ref) for matching actors. If
    the response's `next_cursor` is not null, call this tool again with the same query
    and `cursor` set to that value to fetch the next page.

    IMPORTANT: When searching for logs, use the actor_ref (second element of each tuple)
    with search_logs(actor_ref=...) rather than actor_name. The actor_ref is the unique
    identifier and provides more accurate filtering than actor_name.

    Example workflow:
    1. Call search_actors(query="John") to find actors
    2. Use the actor_ref from the results: search_logs(actor_ref="user:123")
    """
    actors, next_cursor = await log_service.get_log_actor_names(
        search=query,
        authorized_entities=authorized_entities,
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedMcpResponse(items=actors, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_resources(
    query: Annotated[str | None, "The query (keywords) to search for resources"],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[tuple[str, str]]:
    """Search for resources on partial name match ("Config" will match "Config Profile 123").

    Returns a paginated list of tuples (resource_name, resource_ref) for matching resources.
    If the response's `next_cursor` is not null, call this tool again with the same query
    and `cursor` set to that value to fetch the next page.

    IMPORTANT: When searching for logs, use the resource_ref (second element of each tuple)
    with search_logs(resource_ref=...) rather than resource_name. The resource_ref is the unique
    identifier and provides more accurate filtering than resource_name.

    Example workflow:
    1. Call search_resources(query="Config") to find resources
    2. Use the resource_ref from the results: search_logs(resource_ref="config:123")
    """
    resources, next_cursor = await log_service.get_log_resource_names(
        search=query,
        authorized_entities=authorized_entities,
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedMcpResponse(items=resources, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_rich_tags(
    query: Annotated[str | None, "The query (keywords) to search for rich tags"],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[tuple[str, str]]:
    """Search for rich tags on partial name match ("abc" will match "Profile ABC").

    Rich tags are tags that tracks a resource accross logs.

    Returns a paginated list of tuples (tag_name, tag_ref) for matching tags. If the
    response's `next_cursor` is not null, call this tool again with the same query and
    `cursor` set to that value to fetch the next page.

    IMPORTANT: When searching for logs, use the tag_ref (second element of each tuple)
    with search_logs(tag_ref=...) rather than tag_name. The tag_ref is the unique
    identifier and provides more accurate filtering than tag_name.

    Example workflow:
    1. Call search_rich_tags(query="abc") to find tags
    2. Use the tag_ref from the results: search_logs(tag_ref="profile:abc")
    """
    tags, next_cursor = await log_service.get_log_tag_names(
        search=query,
        authorized_entities=authorized_entities,
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedMcpResponse(items=tags, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def search_entities(
    query: Annotated[str, "The query (keywords) to search for entities"],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[LogEntityMcpResponse]:
    """Search for entities on partial name match ("Ent" will match "Entity 1").

    Returns a paginated list of LogEntityMcpResponse for matching entities. If the
    response's `next_cursor` is not null, call this tool again with the same query and
    `cursor` set to that value to fetch the next page.

    When searching for logs on a specific entity:
    - first: call search_entities to get the list of possible entities
    - then: use the ref of the entity with search_logs(entity_ref=ref)
    """
    entities, next_cursor = await log_service.get_log_entities(
        search=query,
        authorized_entities=authorized_entities,
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )

    return PaginatedMcpResponse(
        items=[
            LogEntityMcpResponse(
                ref=entity.ref,
                name=entity.name,
                path=" > ".join(
                    [
                        ent.name
                        async for ent in log_service.iter_on_log_entity_path(entity)
                    ]
                ),
            )
            for entity in entities
        ],
        next_cursor=next_cursor,
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_action_types(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List all possible action types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific action type:
    - first: call list_action_types to get the list of possible action types
    - then: use the action_type with search_logs(action_type=...)
    """
    action_types, next_cursor = await log_service.get_log_action_types(
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=authorized_entities,
    )
    return PaginatedMcpResponse(items=action_types, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_action_categories(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List all possible action categories (action categories are used to group action types).

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific action category:
    - first: call list_action_categories to get the list of possible action categories
    - then: use the action_category with search_logs(action_category=...)
    """
    action_categories, next_cursor = await log_service.get_log_action_categories(
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=authorized_entities,
    )
    return PaginatedMcpResponse(items=action_categories, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_actor_types(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List all possible actor types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific actor type:
    - first: call list_actor_types to get the list of possible actor types
    - then: use the actor_type with search_logs(actor_type=...)
    """
    actor_types, next_cursor = await log_service.get_log_actor_types(
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=authorized_entities,
    )
    return PaginatedMcpResponse(items=actor_types, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_resource_types(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List all possible resource types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific resource type:
    - first: call list_resource_types to get the list of possible resource types
    - then: use the resource_type with search_logs(resource_type=...)
    """
    resource_types, next_cursor = await log_service.get_log_resource_types(
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=authorized_entities,
    )
    return PaginatedMcpResponse(items=resource_types, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_attachment_types(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List all possible attachment types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific attachment type:
    - first: call list_attachment_types to get the list of possible attachment types
    - then: use the attachment_type with search_logs(attachment_type=...)
    """
    attachment_types, next_cursor = await log_service.get_log_attachment_types(
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=authorized_entities,
    )
    return PaginatedMcpResponse(items=attachment_types, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_attachment_mime_types(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List all possible attachment MIME types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific attachment MIME type:
    - first: call list_attachment_mime_types to get the list of possible attachment MIME types
    - then: use the attachment_mime_type with search_logs(attachment_mime_type=...)
    """
    (
        attachment_mime_types,
        next_cursor,
    ) = await log_service.get_log_attachment_mime_types(
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=authorized_entities,
    )
    return PaginatedMcpResponse(items=attachment_mime_types, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_simple_tag_types(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List all possible tag types for simple tags.

    Simple tags are tags without a ref, used purely for categorization (e.g. a tag of type
    "security"). For tags that track a resource across logs (with a name and a ref), use
    search_rich_tags instead.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific simple tag type:
    - first: call list_simple_tag_types to get the list of possible simple tag types
    - then: use the tag_type with search_logs(tag_type=...)
    """
    tag_types, next_cursor = await log_service.get_log_simple_tag_types(
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=authorized_entities,
    )
    return PaginatedMcpResponse(items=tag_types, next_cursor=next_cursor)


async def _list_custom_fields(
    log_service: LogService,
    authorized_entities: set[str],
    get_data_func_name: str,
    cursor: str | None,
) -> PaginatedMcpResponse[CustomFieldData]:
    fields, next_cursor = await getattr(log_service, get_data_func_name)(
        authorized_entities=authorized_entities,
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedMcpResponse(
        items=[CustomFieldData(name=name, type=type_) for name, type_ in fields],
        next_cursor=next_cursor,
    )


async def _list_custom_field_enum_values(
    log_service: LogService,
    authorized_entities: set[str],
    get_data_func_name: str,
    field_name: str,
    cursor: str | None,
) -> PaginatedMcpResponse[str]:
    values, next_cursor = await getattr(log_service, get_data_func_name)(
        field_name=field_name,
        authorized_entities=authorized_entities,
        limit=DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedMcpResponse(items=values, next_cursor=next_cursor)


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_source_fields(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[CustomFieldData]:
    """List the available custom field names under "source", along with their type.

    Use this before filtering search_logs(search_params={"source": {...}}), to discover
    which field names actually exist in this repository.

    If a field's type is "enum", call list_source_field_values(field_name) to get its
    possible values. Other types (string, datetime, boolean, integer, float, json) have
    unbounded values and must be filtered with a value already known (e.g. found in a
    previous search_logs result).

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_fields(
        log_service, authorized_entities, "get_log_source_fields", cursor
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_source_field_values(
    field_name: Annotated[str, "The field name, as returned by list_source_fields"],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List the distinct known values for one "source" custom field.

    Only meaningful for fields whose type is "enum" (see list_source_fields) — for any
    other type this returns an empty list.

    Example workflow:
    1. list_source_fields() -> [{"name": "status", "type": "enum"}, ...]
    2. list_source_field_values(field_name="status") -> ["enabled", "disabled"]
    3. search_logs(search_params={"source": {"status": "enabled"}})

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with the same field_name and `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_field_enum_values(
        log_service, authorized_entities, "get_source_enum_values", field_name, cursor
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_details_fields(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[CustomFieldData]:
    """List the available custom field names under "details", along with their type.

    Use this before filtering search_logs(search_params={"details": {...}}), to discover
    which field names actually exist in this repository.

    If a field's type is "enum", call list_detail_field_values(field_name) to get its
    possible values. Other types (string, datetime, boolean, integer, float, json) have
    unbounded values and must be filtered with a value already known (e.g. found in a
    previous search_logs result).

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_fields(
        log_service, authorized_entities, "get_log_details_fields", cursor
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_detail_field_values(
    field_name: Annotated[str, "The field name, as returned by list_details_fields"],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List the distinct known values for one "details" custom field.

    Only meaningful for fields whose type is "enum" (see list_details_fields) — for any
    other type this returns an empty list.

    Example workflow:
    1. list_details_fields() -> [{"name": "status", "type": "enum"}, ...]
    2. list_detail_field_values(field_name="status") -> ["enabled", "disabled"]
    3. search_logs(search_params={"details": {"status": "enabled"}})

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with the same field_name and `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_field_enum_values(
        log_service, authorized_entities, "get_details_enum_values", field_name, cursor
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_actor_extra_fields(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[CustomFieldData]:
    """List the available custom field names under "actor_extra", along with their type.

    Use this before filtering search_logs(search_params={"actor_extra": {...}}), to discover
    which field names actually exist in this repository.

    If a field's type is "enum", call list_actor_extra_field_values(field_name) to get its
    possible values. Other types (string, datetime, boolean, integer, float, json) have
    unbounded values and must be filtered with a value already known (e.g. found in a
    previous search_logs result).

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_fields(
        log_service, authorized_entities, "get_log_actor_extra_fields", cursor
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_actor_extra_field_values(
    field_name: Annotated[
        str, "The field name, as returned by list_actor_extra_fields"
    ],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List the distinct known values for one "actor_extra" custom field.

    Only meaningful for fields whose type is "enum" (see list_actor_extra_fields) — for any
    other type this returns an empty list.

    Example workflow:
    1. list_actor_extra_fields() -> [{"name": "department", "type": "enum"}, ...]
    2. list_actor_extra_field_values(field_name="department") -> ["IT", "HR"]
    3. search_logs(search_params={"actor_extra": {"department": "IT"}})

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with the same field_name and `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_field_enum_values(
        log_service,
        authorized_entities,
        "get_actor_extra_enum_values",
        field_name,
        cursor,
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_resource_extra_fields(
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[CustomFieldData]:
    """List the available custom field names under "resource_extra", along with their type.

    Use this before filtering search_logs(search_params={"resource_extra": {...}}), to discover
    which field names actually exist in this repository.

    If a field's type is "enum", call list_resource_extra_field_values(field_name) to get its
    possible values. Other types (string, datetime, boolean, integer, float, json) have
    unbounded values and must be filtered with a value already known (e.g. found in a
    previous search_logs result).

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_fields(
        log_service, authorized_entities, "get_log_resource_extra_fields", cursor
    )


@mcp.tool(annotations=TOOL_ANNOTATIONS)
async def list_resource_extra_field_values(
    field_name: Annotated[
        str, "The field name, as returned by list_resource_extra_fields"
    ],
    cursor: Annotated[str | None, CURSOR_PARAM_DESCRIPTION] = None,
    log_service: LogService = Depends(get_log_service),
    authorized_entities: set[str] = Depends(get_authorized_entities),
) -> PaginatedMcpResponse[str]:
    """List the distinct known values for one "resource_extra" custom field.

    Only meaningful for fields whose type is "enum" (see list_resource_extra_fields) — for
    any other type this returns an empty list.

    Example workflow:
    1. list_resource_extra_fields() -> [{"name": "environment", "type": "enum"}, ...]
    2. list_resource_extra_field_values(field_name="environment") -> ["production", "staging"]
    3. search_logs(search_params={"resource_extra": {"environment": "production"}})

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with the same field_name and `cursor` set to that value to fetch the next page.
    """
    return await _list_custom_field_enum_values(
        log_service,
        authorized_entities,
        "get_resource_extra_enum_values",
        field_name,
        cursor,
    )
