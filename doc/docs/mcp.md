# MCP Server

Auditize exposes an [MCP](https://modelcontextprotocol.io/) server that lets agentic tools such as Claude explore the logs of a repository directly, using natural language.

## Connecting to the MCP server

The MCP server is served over streamable HTTP at `${AUDITIZE_URL}/mcp/logs`. Two headers are required on every request:

- `Authorization: Bearer ${AUDITIZE_APIKEY}`, where `${AUDITIZE_APIKEY}` is the secret of an [API key](overview.md#api-keys) with at least read permission on the [log repository](overview.md#log-repositories) you want to explore.
- `X-Auditize-Repo: ${AUDITIZE_REPO}`, the ID of the repository to explore. The MCP server operates on a single repository at a time.

If the API key is restricted to a subset of [log entities](overview.md#log-repositories), the results returned by the tools are filtered accordingly.

Refer to your agentic tool's own documentation for how to connect it to an MCP server (some tools support remote HTTP servers directly, others require a local bridge).

## Available tools

The MCP server exposes the following read-only tools:

| Tool | Description | Parameters |
|---|---|---|
| `describe_repo` | Overview of the repository: log count, time range, action/actor/resource types, custom fields catalog | Time window |
| `describe_action` | Details on one action type: count, actor/resource types, custom fields with coverage, values and ranges | An action type, time window |
| `search_logs` | Search logs (paginated) | Log filters, time window |
| `count_logs` | Count logs matching the filters | Log filters, time window |
| `aggregate_logs` | Count logs grouped by 1 or 2 dimensions (top N, breakdown) | Dimensions to group by, log filters, time window, max number of groups |
| `aggregate_logs_over_time` | Count logs per period or per hour of day / day of week | Period duration, log filters, time window, timezone, dimension to break down each period by, dimension to count distinct values of |
| `search_actors`, `search_resources`, `search_rich_tags`, `search_entities` | Resolve names into refs usable as filters (paginated) | Part of a name |
| `list_action_types`, `list_action_categories`, `list_actor_types`, `list_resource_types`, `list_attachment_types`, `list_attachment_mime_types`, `list_simple_tag_types` | List the possible values of these filters (paginated) | — |
| `list_source_fields`, `list_details_fields`, `list_actor_extra_fields`, `list_resource_extra_fields` | List custom fields with their type (paginated) | — |
| `list_source_field_values`, `list_detail_field_values`, `list_actor_extra_field_values`, `list_resource_extra_field_values` | List the values of an enum custom field (paginated) | A custom field name |
