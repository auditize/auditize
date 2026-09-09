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

- `search_logs` and `count_logs`, to search and count logs using the same filters as the [REST API](sending-logs.md).
- `search_actors`, `search_resources`, `search_rich_tags` and `search_entities`, to resolve names into refs usable as filters in `search_logs`/`count_logs`.
- `list_action_types`, `list_action_categories`, `list_actor_types`, `list_resource_types`, `list_attachment_types`, `list_attachment_mime_types` and `list_simple_tag_types`, to discover the possible values for these filters.
- `list_source_fields`, `list_details_fields`, `list_actor_extra_fields`, `list_resource_extra_fields` and their `*_field_values` counterparts, to discover and filter on custom fields.

Listing and search tools are paginated with cursor-based pagination.
