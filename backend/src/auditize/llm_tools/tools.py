from datetime import datetime
from typing import Annotated

from pydantic import Field

from auditize.llm_tools.models import (
    ActionDescription,
    LogAggregationToolResponse,
    LogEntityToolResponse,
    LogTimeAggregationToolResponse,
    PaginatedToolResponse,
    RepoDescription,
)
from auditize.llm_tools.service import ToolContext
from auditize.log.models import (
    CustomFieldData,
    LogResponse,
    LogSearchParams,
)
from auditize.log.service import (
    AGGREGATION_BUILTIN_DIMENSIONS,
    CUSTOM_FIELD_GROUPS,
    LogTimePeriod,
    TimeAggregationInterval,
)

# Page size used by all tools, except search_logs which returns heavier objects.
_DEFAULT_TOOL_PAGE_LIMIT = 50
_SEARCH_LOGS_PAGE_LIMIT = 10

_CURSOR_PARAM_DESCRIPTION = (
    "Pagination cursor from a previous call's next_cursor field. "
    "Leave unset to get the first page."
)


_AGGREGATION_DIMENSION_DESCRIPTION = (
    "A dimension is either one of "
    f"{', '.join(AGGREGATION_BUILTIN_DIMENSIONS)} or a custom field as "
    "<group>.<field_name> with group one of "
    f"{', '.join(CUSTOM_FIELD_GROUPS)} (e.g. details.status, actor.role)"
)


async def search_logs(
    ctx: ToolContext,
    search_params: LogSearchParams,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[LogResponse]:
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
    logs, next_cursor = await ctx.log_service.get_logs(
        search_params=search_params,
        authorized_entities=ctx.authorized_entities,
        limit=_SEARCH_LOGS_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedToolResponse(
        items=[LogResponse.model_validate(log.model_dump()) for log in logs],
        next_cursor=next_cursor,
    )


async def count_logs(
    ctx: ToolContext,
    search_params: LogSearchParams,
) -> int:
    """Count the logs in the repository matching optional keywords in the query.

    Takes the same search_params as search_logs, but returns the total number of
    matching logs instead of the logs themselves. Use this when you only need a
    count (e.g. "how many logs...") rather than the log details.

    To filter on custom fields (source, details, actor_extra, resource_extra), first discover
    available field names and their type with list_source_fields / list_details_fields /
    list_actor_extra_fields / list_resource_extra_fields, then for fields of type "enum" get
    their possible values with the matching list_source_field_values / list_detail_field_values /
    list_actor_extra_field_values / list_resource_extra_field_values tool.
    """
    return await ctx.log_service.count_logs(
        search_params=search_params,
        authorized_entities=ctx.authorized_entities,
    )


async def aggregate_logs(
    ctx: ToolContext,
    group_by: Annotated[
        list[str],
        Field(
            min_length=1,
            max_length=2,
            description=(
                "1 or 2 dimensions to group logs by. "
                + _AGGREGATION_DIMENSION_DESCRIPTION
            ),
        ),
    ],
    search_params: LogSearchParams = LogSearchParams(),
    limit: Annotated[
        int, Field(ge=1, le=50, description="Maximum number of rows to return")
    ] = 10,
) -> LogAggregationToolResponse:
    """Count logs grouped by one or two dimensions, using the same filters as search_logs.

    Use it for "top N" and "breakdown by" questions instead of paging through
    search_logs. Returns a flat list of rows, one per group (one per combination of
    values with two dimensions), sorted by count and limited to the top `limit`, plus
    `other_count` (logs that are not in the returned rows). Logs without value for a
    dimension are not part of any group and are counted in `other_count`.

    Custom fields (source.<field_name>, details.<field_name>, actor.<field_name>,
    resource.<field_name>) can be used as dimensions if they are of type string,
    enum, boolean, integer or float. Discover available field names and their type
    with list_source_fields / list_details_fields / list_actor_extra_fields /
    list_resource_extra_fields. String values are grouped as is (case-sensitive),
    values longer than 1024 characters are not part of any group.

    Dimension values in rows are:
    - a scalar for action_type, action_category, actor_type and resource_type
    - {ref, name} for actor and resource (name is the most recent one among the
      logs of the group)
    - a string, boolean, integer or float for custom fields of type string / enum,
      boolean, integer or float respectively
    """
    aggregation = await ctx.log_service.aggregate_logs(
        group_by=group_by,
        search_params=search_params,
        authorized_entities=ctx.authorized_entities,
        limit=limit,
    )

    return LogAggregationToolResponse(
        total_count=aggregation.total_count,
        rows=[
            {**dict(zip(group_by, values)), "count": count}
            for values, count in aggregation.rows
        ],
        other_count=aggregation.other_count,
    )


def _build_time_period_entry(
    period: LogTimePeriod, split_by: str | None, count_distinct: str | None
) -> dict:
    # distinct_count, breakdown and other_count are only set when the matching
    # option is used
    entry = {"period": period.period, "count": period.count}
    if count_distinct:
        entry["distinct_count"] = period.distinct_count
    if split_by:
        entry["breakdown"] = []
        for value, count, distinct_count in period.breakdown:
            breakdown_entry = {split_by: value, "count": count}
            if count_distinct:
                breakdown_entry["distinct_count"] = distinct_count
            entry["breakdown"].append(breakdown_entry)
        entry["other_count"] = period.other_count
    return entry


async def aggregate_logs_over_time(
    ctx: ToolContext,
    interval: Annotated[
        TimeAggregationInterval,
        Field(
            description=(
                "Duration of each period, or hour_of_day / day_of_week "
                "to get the activity profile over the hours of the day / the days of "
                "the week across the whole time window"
            )
        ),
    ],
    search_params: LogSearchParams = LogSearchParams(),
    timezone: Annotated[
        str,
        Field(
            description=(
                "IANA timezone (e.g. Europe/Paris) used to align periods and to "
                "compute hours of day / days of week"
            )
        ),
    ] = "UTC",
    split_by: Annotated[
        str | None,
        Field(
            description=(
                "Optional dimension to break down each period by its top values. "
                + _AGGREGATION_DIMENSION_DESCRIPTION
            )
        ),
    ] = None,
    split_limit: Annotated[
        int,
        Field(
            ge=1,
            le=10,
            description=(
                "Number of top values of split_by (top values are computed over "
                "the whole time window)"
            ),
        ),
    ] = 5,
    count_distinct: Annotated[
        str | None,
        Field(
            description=(
                "Optional dimension whose distinct values are counted in each period "
                "(not available with hour_of_day / day_of_week). "
                + _AGGREGATION_DIMENSION_DESCRIPTION
            )
        ),
    ] = None,
) -> LogTimeAggregationToolResponse:
    """Count logs per period of time, using the same filters as search_logs.

    Use it for "when" and "how does it evolve" questions instead of paging through
    search_logs:
    - periods of a fixed duration (1_minute to 1_month) to spot spikes or gaps
    - hour_of_day / day_of_week to get the activity profile across the time window
    - split_by to see which top values of a dimension (e.g. actor) contribute to
      each period
    - count_distinct to count distinct values of a dimension (e.g. actor, resource)
      per period

    The time window is given by search_params.since / until (or by the oldest / most
    recent matching log if not set). The number of periods is limited (and lower with
    split_by, depending on split_limit): if the tool reports too many periods, narrow
    the time window, use a larger interval or reduce split_limit.

    Every period is returned, including periods without logs. With split_by, each
    period only contains the top values having logs in that period (use
    aggregate_logs to get their total counts). Dimension values are formatted like in
    aggregate_logs. Distinct counts are approximate above ~3000 distinct values.

    Custom fields (source.<field_name>, details.<field_name>, actor.<field_name>,
    resource.<field_name>) can be used as dimensions if they are of type string,
    enum, boolean, integer or float. Discover available field names and their type
    with list_source_fields / list_details_fields / list_actor_extra_fields /
    list_resource_extra_fields. String values are grouped as is (case-sensitive),
    values longer than 1024 characters are not part of any group.
    """
    aggregation = await ctx.log_service.aggregate_logs_over_time(
        interval=interval,
        timezone_name=timezone,
        split_by=split_by,
        split_limit=split_limit,
        count_distinct=count_distinct,
        search_params=search_params,
        authorized_entities=ctx.authorized_entities,
    )

    return LogTimeAggregationToolResponse(
        interval=interval.value,
        timezone=timezone,
        start=aggregation.start,
        end=aggregation.end,
        total_count=aggregation.total_count,
        timeline=[
            _build_time_period_entry(period, split_by, count_distinct)
            for period in aggregation.timeline
        ],
    )


_SINCE_PARAM_DESCRIPTION = "Only take into account logs emitted at or after this date"
_UNTIL_PARAM_DESCRIPTION = "Only take into account logs emitted at or before this date"


async def describe_repo(
    ctx: ToolContext,
    since: Annotated[
        datetime | None, Field(description=_SINCE_PARAM_DESCRIPTION)
    ] = None,
    until: Annotated[
        datetime | None, Field(description=_UNTIL_PARAM_DESCRIPTION)
    ] = None,
) -> RepoDescription:
    """Get a compact overview of the repository: number of logs, time range, action types
    (with category and count), actor types and resource types (with count and number of
    distinct actors/resources), and the catalog of custom fields (source, details, actor,
    resource) with their type.

    Call this first when exploring a repository you don't know yet: it replaces
    list_action_types, list_actor_types, list_resource_types and list_*_fields.

    It does not return field values, value ranges or field coverage: call
    describe_action(action_type) for the action types relevant to your question.

    since / until restrict everything (counts, time range and field catalog) to the
    logs emitted within that window.
    """
    return await ctx.log_service.describe_repo(
        authorized_entities=ctx.authorized_entities, since=since, until=until
    )


async def describe_action(
    ctx: ToolContext,
    action_type: Annotated[str, Field(description="The action type to describe")],
    since: Annotated[
        datetime | None, Field(description=_SINCE_PARAM_DESCRIPTION)
    ] = None,
    until: Annotated[
        datetime | None, Field(description=_UNTIL_PARAM_DESCRIPTION)
    ] = None,
) -> ActionDescription:
    """Describe the logs of one action type: count, time range, actor and resource types,
    and every custom field actually present in these logs with its coverage (share of
    logs having the field), number of distinct values, its values with their counts
    (when there are at most 20) and its min/max range (numeric and datetime fields).

    Use it after describe_repo, for the action types relevant to your question, before
    filtering or aggregating on custom fields. It usually replaces several
    list_*_field_values and aggregate_logs calls.
    """
    return await ctx.log_service.describe_action(
        action_type,
        authorized_entities=ctx.authorized_entities,
        since=since,
        until=until,
    )


async def search_actors(
    ctx: ToolContext,
    query: Annotated[str | None, "The query (keywords) to search for actors"],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[tuple[str, str]]:
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
    actors, next_cursor = await ctx.log_service.get_log_actor_names(
        search=query,
        authorized_entities=ctx.authorized_entities,
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedToolResponse(items=actors, next_cursor=next_cursor)


async def search_resources(
    ctx: ToolContext,
    query: Annotated[str | None, "The query (keywords) to search for resources"],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[tuple[str, str]]:
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
    resources, next_cursor = await ctx.log_service.get_log_resource_names(
        search=query,
        authorized_entities=ctx.authorized_entities,
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedToolResponse(items=resources, next_cursor=next_cursor)


async def search_rich_tags(
    ctx: ToolContext,
    query: Annotated[str | None, "The query (keywords) to search for rich tags"],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[tuple[str, str]]:
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
    tags, next_cursor = await ctx.log_service.get_log_tag_names(
        search=query,
        authorized_entities=ctx.authorized_entities,
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedToolResponse(items=tags, next_cursor=next_cursor)


async def search_entities(
    ctx: ToolContext,
    query: Annotated[str, "The query (keywords) to search for entities"],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[LogEntityToolResponse]:
    """Search for entities on partial name match ("Ent" will match "Entity 1").

    Returns a paginated list of LogEntityToolResponse for matching entities. If the
    response's `next_cursor` is not null, call this tool again with the same query and
    `cursor` set to that value to fetch the next page.

    When searching for logs on a specific entity:
    - first: call search_entities to get the list of possible entities
    - then: use the ref of the entity with search_logs(entity_ref=ref)
    """
    entities, next_cursor = await ctx.log_service.get_log_entities(
        search=query,
        authorized_entities=ctx.authorized_entities,
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )

    return PaginatedToolResponse(
        items=[
            LogEntityToolResponse(
                ref=entity.ref,
                name=entity.name,
                path=" > ".join(
                    [
                        ent.name
                        async for ent in ctx.log_service.iter_on_log_entity_path(entity)
                    ]
                ),
            )
            for entity in entities
        ],
        next_cursor=next_cursor,
    )


async def list_action_types(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
    """List all possible action types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific action type:
    - first: call list_action_types to get the list of possible action types
    - then: use the action_type with search_logs(action_type=...)
    """
    action_types, next_cursor = await ctx.log_service.get_log_action_types(
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=ctx.authorized_entities,
    )
    return PaginatedToolResponse(items=action_types, next_cursor=next_cursor)


async def list_action_categories(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
    """List all possible action categories (action categories are used to group action types).

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific action category:
    - first: call list_action_categories to get the list of possible action categories
    - then: use the action_category with search_logs(action_category=...)
    """
    action_categories, next_cursor = await ctx.log_service.get_log_action_categories(
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=ctx.authorized_entities,
    )
    return PaginatedToolResponse(items=action_categories, next_cursor=next_cursor)


async def list_actor_types(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
    """List all possible actor types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific actor type:
    - first: call list_actor_types to get the list of possible actor types
    - then: use the actor_type with search_logs(actor_type=...)
    """
    actor_types, next_cursor = await ctx.log_service.get_log_actor_types(
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=ctx.authorized_entities,
    )
    return PaginatedToolResponse(items=actor_types, next_cursor=next_cursor)


async def list_resource_types(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
    """List all possible resource types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific resource type:
    - first: call list_resource_types to get the list of possible resource types
    - then: use the resource_type with search_logs(resource_type=...)
    """
    resource_types, next_cursor = await ctx.log_service.get_log_resource_types(
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=ctx.authorized_entities,
    )
    return PaginatedToolResponse(items=resource_types, next_cursor=next_cursor)


async def list_attachment_types(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
    """List all possible attachment types.

    Results are paginated. If the response's `next_cursor` is not null, call this tool
    again with `cursor` set to that value to fetch the next page.

    When searching for logs on a specific attachment type:
    - first: call list_attachment_types to get the list of possible attachment types
    - then: use the attachment_type with search_logs(attachment_type=...)
    """
    attachment_types, next_cursor = await ctx.log_service.get_log_attachment_types(
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=ctx.authorized_entities,
    )
    return PaginatedToolResponse(items=attachment_types, next_cursor=next_cursor)


async def list_attachment_mime_types(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
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
    ) = await ctx.log_service.get_log_attachment_mime_types(
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=ctx.authorized_entities,
    )
    return PaginatedToolResponse(items=attachment_mime_types, next_cursor=next_cursor)


async def list_simple_tag_types(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
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
    tag_types, next_cursor = await ctx.log_service.get_log_simple_tag_types(
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
        authorized_entities=ctx.authorized_entities,
    )
    return PaginatedToolResponse(items=tag_types, next_cursor=next_cursor)


async def _list_custom_fields(
    ctx: ToolContext,
    get_data_func_name: str,
    cursor: str | None,
) -> PaginatedToolResponse[CustomFieldData]:
    fields, next_cursor = await getattr(ctx.log_service, get_data_func_name)(
        authorized_entities=ctx.authorized_entities,
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedToolResponse(
        items=[CustomFieldData(name=name, type=type_) for name, type_ in fields],
        next_cursor=next_cursor,
    )


async def _list_custom_field_enum_values(
    ctx: ToolContext,
    get_data_func_name: str,
    field_name: str,
    cursor: str | None,
) -> PaginatedToolResponse[str]:
    values, next_cursor = await getattr(ctx.log_service, get_data_func_name)(
        field_name=field_name,
        authorized_entities=ctx.authorized_entities,
        limit=_DEFAULT_TOOL_PAGE_LIMIT,
        pagination_cursor=cursor,
    )
    return PaginatedToolResponse(items=values, next_cursor=next_cursor)


async def list_source_fields(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[CustomFieldData]:
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
    return await _list_custom_fields(ctx, "get_log_source_fields", cursor)


async def list_source_field_values(
    ctx: ToolContext,
    field_name: Annotated[str, "The field name, as returned by list_source_fields"],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
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
        ctx, "get_source_enum_values", field_name, cursor
    )


async def list_details_fields(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[CustomFieldData]:
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
    return await _list_custom_fields(ctx, "get_log_details_fields", cursor)


async def list_detail_field_values(
    ctx: ToolContext,
    field_name: Annotated[str, "The field name, as returned by list_details_fields"],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
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
        ctx, "get_details_enum_values", field_name, cursor
    )


async def list_actor_extra_fields(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[CustomFieldData]:
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
    return await _list_custom_fields(ctx, "get_log_actor_extra_fields", cursor)


async def list_actor_extra_field_values(
    ctx: ToolContext,
    field_name: Annotated[
        str, "The field name, as returned by list_actor_extra_fields"
    ],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
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
        ctx,
        "get_actor_extra_enum_values",
        field_name,
        cursor,
    )


async def list_resource_extra_fields(
    ctx: ToolContext,
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[CustomFieldData]:
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
    return await _list_custom_fields(ctx, "get_log_resource_extra_fields", cursor)


async def list_resource_extra_field_values(
    ctx: ToolContext,
    field_name: Annotated[
        str, "The field name, as returned by list_resource_extra_fields"
    ],
    cursor: Annotated[str | None, _CURSOR_PARAM_DESCRIPTION] = None,
) -> PaginatedToolResponse[str]:
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
        ctx,
        "get_resource_extra_enum_values",
        field_name,
        cursor,
    )


LOG_TOOLS = [
    search_logs,
    count_logs,
    aggregate_logs,
    aggregate_logs_over_time,
    describe_repo,
    describe_action,
    search_actors,
    search_resources,
    search_rich_tags,
    search_entities,
    list_action_types,
    list_action_categories,
    list_actor_types,
    list_resource_types,
    list_attachment_types,
    list_attachment_mime_types,
    list_simple_tag_types,
    list_source_fields,
    list_source_field_values,
    list_details_fields,
    list_detail_field_values,
    list_actor_extra_fields,
    list_actor_extra_field_values,
    list_resource_extra_fields,
    list_resource_extra_field_values,
]
