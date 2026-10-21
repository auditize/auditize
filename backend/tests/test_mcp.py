from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from fastmcp.exceptions import ToolError

from auditize.mcp.app import mcp
from conftest import ApikeyBuilder
from helpers import matchers
from helpers.apikey import PreparedApikey
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


@pytest.fixture
async def mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client


@pytest.fixture
async def log_read_apikey(apikey_builder):
    return await apikey_builder({"logs": {"read": True}})


@contextmanager
def mock_mcp_http_headers(repo: PreparedRepo, apikey: PreparedApikey):
    with patch(
        "auditize.mcp.tools.get_http_headers",
        return_value={
            "x-auditize-repo": repo.id,
            "authorization": f"Bearer {apikey.key}",
        },
    ):
        yield


@dataclass
class ToolCaller:
    repo: PreparedRepo
    apikey: PreparedApikey
    mcp_client: Client[FastMCPTransport]

    async def __call__(self, tool: str, params: dict | None = None) -> Any:
        with mock_mcp_http_headers(self.repo, self.apikey):
            result = await self.mcp_client.call_tool(tool, params or {})
        return result.structured_content


@pytest.fixture
def call_tool(
    repo: PreparedRepo,
    log_read_apikey: PreparedApikey,
    mcp_client: Client[FastMCPTransport],
) -> ToolCaller:
    return ToolCaller(repo, log_read_apikey, mcp_client)


def _action(type_: str, category: str = "category") -> dict:
    return {"action": {"type": type_, "category": category}}


def _actor(ref: str, type_: str = "user", **extra) -> dict:
    return {"actor": {"type": type_, "ref": ref, "name": f"User {ref}", **extra}}


def _resource(ref: str, type_: str = "doc", **extra) -> dict:
    return {"resource": {"type": type_, "ref": ref, "name": f"Doc {ref}", **extra}}


def _custom_field(name: str, value: Any, type_: str) -> dict:
    return {"name": name, "value": value, "type": type_}


def _emitted_at(i: int) -> str:
    return f"2024-01-01T10:{i:02d}:00Z"


async def test_search_logs(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    log_1 = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    log_2 = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    assert await call_tool("search_logs", {"search_params": {"actor_ref": "2"}}) == {
        "items": [log_2.expected_api_response()],
        "next_cursor": None,
    }


async def test_search_logs_limited_permissions(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    log = await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "read": True}]}}
    )

    assert await ToolCaller(repo, apikey, mcp_client)(
        "search_logs", {"search_params": {}}
    ) == {
        "items": [log.expected_api_response()],
        "next_cursor": None,
    }


async def test_search_logs_pagination(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    # emitted_at defaults to "now", so logs created later sort first (search_logs
    # orders by emitted_at desc)
    logs = [await repo.create_log_with(log_rw_client, {}) for _ in range(11)]
    logs.reverse()

    first_page = await call_tool("search_logs", {"search_params": {}})
    assert first_page == {
        "items": [log.expected_api_response() for log in logs[:10]],
        "next_cursor": matchers.String(),
    }

    assert await call_tool(
        "search_logs", {"search_params": {}, "cursor": first_page["next_cursor"]}
    ) == {
        "items": [log.expected_api_response() for log in logs[10:]],
        "next_cursor": None,
    }


async def test_count_logs(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    assert await call_tool("count_logs", {"search_params": {"actor_ref": "2"}}) == {
        "result": 1
    }
    assert await call_tool("count_logs", {"search_params": {}}) == {"result": 2}


async def test_search_actors(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "2", "name": "Jane Doe"}}
    )

    assert await call_tool("search_actors", {"query": "jane"}) == {
        "items": [["Jane Doe", "2"]],
        "next_cursor": None,
    }


async def test_search_resources(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {"resource": {"type": "config", "ref": "cfg-1", "name": "Config Profile 123"}},
    )
    await repo.create_log_with(
        log_rw_client,
        {"resource": {"type": "doc", "ref": "doc-2", "name": "Document Template"}},
    )

    assert await call_tool("search_resources", {"query": "config"}) == {
        "items": [["Config Profile 123", "cfg-1"]],
        "next_cursor": None,
    }


async def test_search_rich_tags(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "security"},
                {"type": "config", "name": "Config Profile 123", "ref": "cfg-1"},
            ]
        },
    )

    assert await call_tool("search_rich_tags", {"query": "prof"}) == {
        "items": [["Config Profile 123", "cfg-1"]],
        "next_cursor": None,
    }


async def test_search_entities(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with_entity_path(log_rw_client, ["Customer", "Organization"])
    assert await call_tool("search_entities", {"query": "orga"}) == {
        "items": [
            {
                "ref": "Organization",
                "name": "Organization",
                "path": "Customer > Organization",
            }
        ],
        "next_cursor": None,
    }


async def test_list_action_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log(log_rw_client)
    assert await call_tool("list_action_types") == {
        "items": ["user_login"],
        "next_cursor": None,
    }


async def test_list_action_categories(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log(log_rw_client)
    assert await call_tool("list_action_categories") == {
        "items": ["authentication"],
        "next_cursor": None,
    }


async def test_list_actor_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client, {"actor": {"type": "user", "ref": "1", "name": "John Smith"}}
    )
    assert await call_tool("list_actor_types") == {
        "items": ["user"],
        "next_cursor": None,
    }


async def test_list_resource_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {"resource": {"type": "config", "ref": "cfg-1", "name": "Config Profile 123"}},
    )
    assert await call_tool("list_resource_types") == {
        "items": ["config"],
        "next_cursor": None,
    }


async def test_list_attachment_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(log_rw_client, type="text_file")
    assert await call_tool("list_attachment_types") == {
        "items": ["text_file"],
        "next_cursor": None,
    }


async def test_list_attachment_mime_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    log = await repo.create_log(log_rw_client)
    await log.upload_attachment(log_rw_client, mime_type="text/plain")
    assert await call_tool("list_attachment_mime_types") == {
        "items": ["text/plain"],
        "next_cursor": None,
    }


async def test_list_simple_tag_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {
            "tags": [
                {"type": "security"},
                {"type": "config", "name": "Config Profile 123", "ref": "cfg-1"},
            ]
        },
    )
    assert await call_tool("list_simple_tag_types") == {
        "items": ["security"],
        "next_cursor": None,
    }


# One field per possible CustomFieldType (see auditize.log.models.CustomFieldType), sorted by
# name since that's the order the "fields" aggregation returns them in (composite agg, asc).
CUSTOM_FIELD_VALUES_BY_TYPE = [
    ("boolean_field", True, "boolean"),
    ("datetime_field", "2021-01-01T00:00:00.000Z", "datetime"),
    ("enum_field", "enum_value", "enum"),
    ("float_field", 123.45, "float"),
    ("integer_field", 123, "integer"),
    ("json_field", '{"foo": "bar"}', "json"),
    ("string_field", "string_value", "string"),
]

CUSTOM_FIELD_NAMES_AND_TYPES = [
    (name, field_type) for name, _, field_type in CUSTOM_FIELD_VALUES_BY_TYPE
]

CUSTOM_FIELDS_PAYLOAD = [
    _custom_field(name, value, field_type)
    for name, value, field_type in CUSTOM_FIELD_VALUES_BY_TYPE
]

EXPECTED_CUSTOM_FIELDS = [
    {"name": name, "type": field_type}
    for name, _, field_type in CUSTOM_FIELD_VALUES_BY_TYPE
]


@pytest.fixture
async def log_with_custom_fields(repo: PreparedRepo, log_rw_client: HttpTestHelper):
    return await repo.create_log_with(
        log_rw_client,
        {
            "source": CUSTOM_FIELDS_PAYLOAD,
            "actor": {
                "ref": "actor_ref",
                "type": "actor",
                "name": "Actor",
                "extra": CUSTOM_FIELDS_PAYLOAD,
            },
            "resource": {
                "ref": "resource_ref",
                "type": "resource",
                "name": "Resource",
                "extra": CUSTOM_FIELDS_PAYLOAD,
            },
            "details": CUSTOM_FIELDS_PAYLOAD,
        },
    )


@pytest.mark.usefixtures("log_with_custom_fields")
@pytest.mark.parametrize(
    "tool_name",
    [
        "list_source_fields",
        "list_details_fields",
        "list_actor_extra_fields",
        "list_resource_extra_fields",
    ],
)
async def test_list_custom_fields(
    call_tool: ToolCaller,
    tool_name: str,
):
    assert await call_tool(tool_name) == {
        "items": EXPECTED_CUSTOM_FIELDS,
        "next_cursor": None,
    }


@pytest.mark.usefixtures("log_with_custom_fields")
@pytest.mark.parametrize(
    "tool_name",
    [
        "list_source_field_values",
        "list_detail_field_values",
        "list_actor_extra_field_values",
        "list_resource_extra_field_values",
    ],
)
@pytest.mark.parametrize("field_name,field_type", CUSTOM_FIELD_NAMES_AND_TYPES)
async def test_list_custom_field_values(
    call_tool: ToolCaller,
    tool_name: str,
    field_name: str,
    field_type: str,
):
    expected = ["enum_value"] if field_type == "enum" else []
    assert await call_tool(tool_name, {"field_name": field_name}) == {
        "items": expected,
        "next_cursor": None,
    }


@pytest.mark.parametrize(
    "dimension,build_log_data",
    [
        (
            "action_type",
            lambda value: _action(value, "some_category"),
        ),
        (
            "action_category",
            lambda value: _action("some_action", value),
        ),
        (
            "actor_type",
            lambda value: _actor("ref", value),
        ),
        (
            "resource_type",
            lambda value: _resource("ref", value),
        ),
    ],
)
async def test_aggregate_logs_scalar_dimensions(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
    dimension: str,
    build_log_data,
):
    for value in ("value_b", "value_a", "value_b"):
        await repo.create_log_with(log_rw_client, build_log_data(value))

    assert await call_tool("aggregate_logs", {"group_by": [dimension]}) == {
        "total_count": 3,
        "rows": [
            {dimension: "value_b", "count": 2},
            {dimension: "value_a", "count": 1},
        ],
        "other_count": 0,
    }


@pytest.mark.parametrize("dimension", ["actor", "resource"])
async def test_aggregate_logs_by_actor_or_resource(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
    dimension: str,
):
    for user_ref, name in (("1", "John Smith"), ("2", "Jane Doe"), ("1", "John Smith")):
        await repo.create_log_with(
            log_rw_client, {dimension: {"type": "user", "ref": user_ref, "name": name}}
        )

    assert await call_tool("aggregate_logs", {"group_by": [dimension]}) == {
        "total_count": 3,
        "rows": [
            {dimension: {"ref": "1", "name": "John Smith"}, "count": 2},
            {dimension: {"ref": "2", "name": "Jane Doe"}, "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_by_actor_uses_latest_name(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    now = datetime.now(timezone.utc)
    yesterday = now - timedelta(days=1)

    # create the most recent log first to make sure the name does not depend
    # on the insertion order
    await repo.create_log_with(
        log_rw_client,
        {"actor": {"type": "user", "ref": "1", "name": "John Smith"}},
        emitted_at=now,
    )
    await repo.create_log_with(
        log_rw_client,
        {"actor": {"type": "user", "ref": "1", "name": "John"}},
        emitted_at=yesterday,
    )

    assert await call_tool("aggregate_logs", {"group_by": ["actor"]}) == {
        "total_count": 2,
        "rows": [
            {"actor": {"ref": "1", "name": "John Smith"}, "count": 2},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_two_dimensions(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for user_ref, action_type in (
        ("1", "login"),
        ("1", "login"),
        ("1", "login"),
        ("1", "logout"),
        ("2", "login"),
        ("2", "login"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                **_action(action_type, "authentication"),
                **_actor(user_ref),
            },
        )

    assert await call_tool(
        "aggregate_logs", {"group_by": ["actor", "action_type"]}
    ) == {
        "total_count": 6,
        "rows": [
            {
                "actor": {"ref": "1", "name": "User 1"},
                "action_type": "login",
                "count": 3,
            },
            {
                "actor": {"ref": "2", "name": "User 2"},
                "action_type": "login",
                "count": 2,
            },
            {
                "actor": {"ref": "1", "name": "User 1"},
                "action_type": "logout",
                "count": 1,
            },
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_without_value(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(log_rw_client, _actor("1"))
    await repo.create_log_with(log_rw_client, {})
    await repo.create_log_with(log_rw_client, {})

    # logs without actor are not part of any row but are counted in other_count
    assert await call_tool("aggregate_logs", {"group_by": ["actor"]}) == {
        "total_count": 3,
        "rows": [{"actor": {"ref": "1", "name": "User 1"}, "count": 1}],
        "other_count": 2,
    }


async def test_aggregate_logs_without_value_two_dimensions(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    actor = {"type": "user", "ref": "1", "name": "User 1"}
    resource = {"type": "config", "ref": "1", "name": "Resource 1"}
    for extra in (
        {"actor": actor, "resource": resource},
        {"actor": actor},
        {"actor": actor},
        {"resource": resource},
        {"resource": resource},
        {"resource": resource},
        {},
        {},
        {},
        {},
    ):
        await repo.create_log_with(log_rw_client, extra)

    assert await call_tool("aggregate_logs", {"group_by": ["actor", "resource"]}) == {
        "total_count": 10,
        "rows": [
            {
                "actor": {"ref": "1", "name": "User 1"},
                "resource": {"ref": "1", "name": "Resource 1"},
                "count": 1,
            },
        ],
        "other_count": 9,
    }


async def test_aggregate_logs_limit_and_other_count(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for action_type, count in (("a", 5), ("b", 4), ("c", 3), ("d", 2), ("e", 1)):
        for _ in range(count):
            await repo.create_log_with(
                log_rw_client,
                _action(action_type, "authentication"),
            )

    data = await call_tool("aggregate_logs", {"group_by": ["action_type"], "limit": 2})
    assert data == {
        "total_count": 15,
        "rows": [
            {"action_type": "a", "count": 5},
            {"action_type": "b", "count": 4},
        ],
        "other_count": 6,
    }


async def test_aggregate_logs_tie_ordering(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    # Rows are sorted by count desc, then by key asc to break ties
    # ("b" is created before "a" to make sure insertion order is not used)
    for action_type in ("b", "a", "c", "c"):
        await repo.create_log_with(
            log_rw_client,
            _action(action_type, "authentication"),
        )

    assert await call_tool("aggregate_logs", {"group_by": ["action_type"]}) == {
        "total_count": 4,
        "rows": [
            {"action_type": "c", "count": 2},
            {"action_type": "a", "count": 1},
            {"action_type": "b", "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_empty(
    call_tool: ToolCaller,
):
    assert await call_tool("aggregate_logs", {"group_by": ["actor"]}) == {
        "total_count": 0,
        "rows": [],
        "other_count": 0,
    }


async def test_aggregate_logs_with_search_params(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for user_ref, status in (
        ("1", "failure"),
        ("1", "failure"),
        ("1", "success"),
        ("2", "failure"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                **_actor(user_ref),
                "details": [_custom_field("status", status, "enum")],
            },
        )

    assert await call_tool(
        "aggregate_logs",
        {"group_by": ["actor"], "search_params": {"details": {"status": "failure"}}},
    ) == {
        "total_count": 3,
        "rows": [
            {"actor": {"ref": "1", "name": "User 1"}, "count": 2},
            {"actor": {"ref": "2", "name": "User 2"}, "count": 1},
        ],
        "other_count": 0,
    }


def _build_log_data_with_custom_fields(group: str, fields: list[dict]) -> dict:
    match group:
        case "actor":
            return _actor("1", extra=fields)
        case "resource":
            return _resource("1", extra=fields)
        case _:
            return {group: fields}


@pytest.mark.parametrize("group", ["source", "details", "actor", "resource"])
@pytest.mark.parametrize(
    "field_type,values",
    [
        (
            "string",
            [
                "Mozilla/5.0 (X11; Linux x86_64)",
                "Mozilla/5.0 (X11; Linux x86_64)",
                "curl/8.4.0",
            ],
        ),
        ("enum", ["a", "a", "b"]),
        ("boolean", [True, True, False]),
        ("integer", [200, 200, 404]),
        ("float", [1.5, 1.5, 2.5]),
    ],
)
async def test_aggregate_logs_by_custom_field(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
    group: str,
    field_type: str,
    values: list,
):
    for value in values:
        await repo.create_log_with(
            log_rw_client,
            _build_log_data_with_custom_fields(
                group, [_custom_field("field", value, field_type)]
            ),
        )
    # log without the custom field
    await repo.create_log_with(
        log_rw_client, _build_log_data_with_custom_fields(group, [])
    )

    dimension = f"{group}.field"
    assert await call_tool("aggregate_logs", {"group_by": [dimension]}) == {
        "total_count": 4,
        "rows": [
            {dimension: values[0], "count": 2},
            {dimension: values[2], "count": 1},
        ],
        "other_count": 1,
    }


async def test_aggregate_logs_by_two_non_keyword_custom_fields(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for success, code, duration in (
        (True, 200, 1.5),
        (True, 200, 1.5),
        (False, 404, 2.5),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                "details": [
                    _custom_field("success", success, "boolean"),
                    _custom_field("code", code, "integer"),
                    _custom_field("duration", duration, "float"),
                ]
            },
        )

    assert await call_tool(
        "aggregate_logs", {"group_by": ["details.success", "details.code"]}
    ) == {
        "total_count": 3,
        "rows": [
            {"details.success": True, "details.code": 200, "count": 2},
            {"details.success": False, "details.code": 404, "count": 1},
        ],
        "other_count": 0,
    }
    assert await call_tool(
        "aggregate_logs", {"group_by": ["details.duration", "details.success"]}
    ) == {
        "total_count": 3,
        "rows": [
            {"details.duration": 1.5, "details.success": True, "count": 2},
            {"details.duration": 2.5, "details.success": False, "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_by_actor_and_actor_custom_field(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for user_ref, role in (("1", "admin"), ("1", "admin"), ("2", "user")):
        await repo.create_log_with(
            log_rw_client,
            _actor(user_ref, extra=[_custom_field("role", role, "enum")]),
        )

    assert await call_tool("aggregate_logs", {"group_by": ["actor", "actor.role"]}) == {
        "total_count": 3,
        "rows": [
            {
                "actor": {"ref": "1", "name": "User 1"},
                "actor.role": "admin",
                "count": 2,
            },
            {"actor": {"ref": "2", "name": "User 2"}, "actor.role": "user", "count": 1},
        ],
        "other_count": 0,
    }


async def test_aggregate_logs_by_custom_field_with_search_params(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for action_type, status in (
        ("login", "failure"),
        ("login", "failure"),
        ("login", "success"),
        ("logout", "failure"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                **_action(action_type, "authentication"),
                "details": [_custom_field("status", status, "enum")],
            },
        )

    assert await call_tool(
        "aggregate_logs",
        {
            "group_by": ["action_type", "details.status"],
            "search_params": {"action_type": "login"},
        },
    ) == {
        "total_count": 3,
        "rows": [
            {"action_type": "login", "details.status": "failure", "count": 2},
            {"action_type": "login", "details.status": "success", "count": 1},
        ],
        "other_count": 0,
    }


@pytest.mark.parametrize("field_type", ["json", "datetime"])
async def test_aggregate_logs_by_custom_field_unsupported_type(
    log_with_custom_fields,
    call_tool: ToolCaller,
    field_type: str,
):
    with pytest.raises(ToolError, match="cannot be used as dimension"):
        await call_tool("aggregate_logs", {"group_by": [f"details.{field_type}_field"]})


async def test_aggregate_logs_by_unknown_custom_field(
    log_with_custom_fields,
    call_tool: ToolCaller,
):
    with pytest.raises(ToolError, match="Unknown custom field"):
        await call_tool("aggregate_logs", {"group_by": ["details.unknown"]})


@pytest.mark.parametrize(
    "group_by",
    [
        ["unknown_group.enum_field"],
        ["details."],
        ["details.enum_field", "details.enum_field"],
    ],
)
async def test_aggregate_logs_by_custom_field_invalid_group_by(
    log_with_custom_fields,
    call_tool: ToolCaller,
    group_by: list[str],
):
    with pytest.raises(ToolError):
        await call_tool("aggregate_logs", {"group_by": group_by})


async def test_aggregate_logs_limited_permissions(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(log_rw_client, _action("login", "authentication"))
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "read": True}]}}
    )

    assert await ToolCaller(repo, apikey, mcp_client)(
        "aggregate_logs", {"group_by": ["action_type"]}
    ) == {
        "total_count": 1,
        "rows": [{"action_type": "login", "count": 1}],
        "other_count": 0,
    }


async def test_aggregate_logs_entity_restricted(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with_entity_path(log_rw_client, ["entity_A"])
    await repo.create_log_with_entity_path(log_rw_client, ["entity_A", "entity_A1"])
    await repo.create_log_with_entity_path(log_rw_client, ["entity_B"])
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "readable_entities": ["entity_A"]}]}}
    )

    assert await ToolCaller(repo, apikey, mcp_client)(
        "aggregate_logs", {"group_by": ["action_type"]}
    ) == {
        "total_count": 2,
        "rows": [{"action_type": "user_login", "count": 2}],
        "other_count": 0,
    }


async def test_aggregate_logs_no_permission(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    mcp_client: Client[FastMCPTransport],
):
    apikey = await apikey_builder({})
    with pytest.raises(ToolError, match="permission"):
        await ToolCaller(repo, apikey, mcp_client)(
            "aggregate_logs", {"group_by": ["action_type"]}
        )


async def test_aggregate_logs_invalid_group_by(
    call_tool: ToolCaller,
):
    with pytest.raises(ToolError):
        await call_tool("aggregate_logs", {"group_by": ["unknown_dimension"]})


async def test_aggregate_logs_invalid_limit(
    call_tool: ToolCaller,
):
    with pytest.raises(ToolError):
        await call_tool("aggregate_logs", {"group_by": ["action_type"], "limit": 51})


async def test_aggregate_logs_over_time_histogram(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at in (
        "2026-01-15T08:30:00Z",  # outside the time window
        "2026-01-15T10:05:00Z",
        "2026-01-15T10:20:00Z",
        "2026-01-15T12:30:00Z",
        "2026-01-15T13:30:00Z",  # outside the time window
    ):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    assert await call_tool(
        "aggregate_logs_over_time",
        {
            "interval": "1_hour",
            "search_params": {
                "since": "2026-01-15T09:00:00Z",
                "until": "2026-01-15T12:59:59Z",
            },
        },
    ) == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T09:00:00Z",
        "end": "2026-01-15T12:59:59Z",
        "total_count": 3,
        "timeline": [
            {"period": "2026-01-15T09:00:00Z", "count": 0},
            {"period": "2026-01-15T10:00:00Z", "count": 2},
            {"period": "2026-01-15T11:00:00Z", "count": 0},
            {"period": "2026-01-15T12:00:00Z", "count": 1},
        ],
    }


async def test_aggregate_logs_over_time_window_from_logs(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at in ("2026-01-15T10:05:00Z", "2026-01-15T12:30:00Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    assert await call_tool("aggregate_logs_over_time", {"interval": "1_hour"}) == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T10:05:00Z",
        "end": "2026-01-15T12:30:00Z",
        "total_count": 2,
        "timeline": [
            {"period": "2026-01-15T10:00:00Z", "count": 1},
            {"period": "2026-01-15T11:00:00Z", "count": 0},
            {"period": "2026-01-15T12:00:00Z", "count": 1},
        ],
    }

    # only "since" is given, "until" is the date of the most recent log
    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "1_hour", "search_params": {"since": "2026-01-15T11:00:00Z"}},
    )
    assert data == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T11:00:00Z",
        "end": "2026-01-15T12:30:00Z",
        "total_count": 1,
        "timeline": [
            {"period": "2026-01-15T11:00:00Z", "count": 0},
            {"period": "2026-01-15T12:00:00Z", "count": 1},
        ],
    }


async def test_aggregate_logs_over_time_empty(
    call_tool: ToolCaller,
):
    assert await call_tool(
        "aggregate_logs_over_time", {"interval": "1_hour", "split_by": "actor"}
    ) == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": None,
        "end": None,
        "total_count": 0,
        "timeline": [],
    }

    assert await call_tool(
        "aggregate_logs_over_time", {"interval": "day_of_week", "split_by": "actor"}
    ) == {
        "interval": "day_of_week",
        "timezone": "UTC",
        "start": None,
        "end": None,
        "total_count": 0,
        "timeline": [
            {"period": period, "count": 0, "breakdown": [], "other_count": 0}
            for period in [
                "monday",
                "tuesday",
                "wednesday",
                "thursday",
                "friday",
                "saturday",
                "sunday",
            ]
        ],
    }


async def test_aggregate_logs_over_time_empty_with_time_window(
    call_tool: ToolCaller,
):
    data = await call_tool(
        "aggregate_logs_over_time",
        {
            "interval": "1_day",
            "search_params": {
                "since": "2026-01-15T00:00:00Z",
                "until": "2026-01-16T23:59:59Z",
            },
            "count_distinct": "actor",
        },
    )
    assert data == {
        "interval": "1_day",
        "timezone": "UTC",
        "start": "2026-01-15T00:00:00Z",
        "end": "2026-01-16T23:59:59Z",
        "total_count": 0,
        "timeline": [
            {"period": "2026-01-15T00:00:00Z", "count": 0, "distinct_count": 0},
            {"period": "2026-01-16T00:00:00Z", "count": 0, "distinct_count": 0},
        ],
    }


async def test_aggregate_logs_over_time_daily_with_timezone(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    # 2026-01-15 23:30 and 2026-01-16 00:30 in Europe/Paris (UTC+1)
    for emitted_at in ("2026-01-15T22:30:00Z", "2026-01-15T23:30:00Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    assert await call_tool(
        "aggregate_logs_over_time",
        {
            "interval": "1_day",
            "timezone": "Europe/Paris",
            "search_params": {
                "since": "2026-01-14T23:00:00Z",
                "until": "2026-01-16T22:59:59Z",
            },
        },
    ) == {
        "interval": "1_day",
        "timezone": "Europe/Paris",
        "start": "2026-01-15T00:00:00+01:00",
        "end": "2026-01-16T23:59:59+01:00",
        "total_count": 2,
        "timeline": [
            {"period": "2026-01-15T00:00:00+01:00", "count": 1},
            {"period": "2026-01-16T00:00:00+01:00", "count": 1},
        ],
    }


async def test_aggregate_logs_over_time_hour_of_day(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at in (
        "2026-01-15T02:10:00Z",  # 03:10 in Europe/Paris
        "2026-01-16T02:50:00Z",  # 03:50 in Europe/Paris
        "2026-01-17T13:00:00Z",  # 14:00 in Europe/Paris
    ):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "hour_of_day", "timezone": "Europe/Paris"},
    )
    expected_timeline = [{"period": period, "count": 0} for period in range(24)]
    expected_timeline[3]["count"] = 2
    expected_timeline[14]["count"] = 1
    assert data == {
        "interval": "hour_of_day",
        "timezone": "Europe/Paris",
        "start": "2026-01-15T03:10:00+01:00",
        "end": "2026-01-17T14:00:00+01:00",
        "total_count": 3,
        "timeline": expected_timeline,
    }


async def test_aggregate_logs_over_time_hour_of_day_across_dst_change(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    # Europe/Paris switches from UTC+1 to UTC+2 on 2026-03-29
    for emitted_at in ("2026-03-28T08:00:00Z", "2026-03-30T07:00:00Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "hour_of_day", "timezone": "Europe/Paris"},
    )
    expected_timeline = [{"period": period, "count": 0} for period in range(24)]
    expected_timeline[9]["count"] = 2
    assert data == {
        "interval": "hour_of_day",
        "timezone": "Europe/Paris",
        "start": "2026-03-28T09:00:00+01:00",
        "end": "2026-03-30T09:00:00+02:00",
        "total_count": 2,
        "timeline": expected_timeline,
    }


async def test_aggregate_logs_over_time_day_of_week(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at in (
        "2026-01-12T10:00:00Z",  # monday
        "2026-01-17T23:30:00Z",  # saturday in UTC, sunday in Europe/Paris
        "2026-01-19T10:00:00Z",  # monday
    ):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "day_of_week", "timezone": "Europe/Paris"},
    )
    assert data == {
        "interval": "day_of_week",
        "timezone": "Europe/Paris",
        "start": "2026-01-12T11:00:00+01:00",
        "end": "2026-01-19T11:00:00+01:00",
        "total_count": 3,
        "timeline": [
            {"period": "monday", "count": 2},
            {"period": "tuesday", "count": 0},
            {"period": "wednesday", "count": 0},
            {"period": "thursday", "count": 0},
            {"period": "friday", "count": 0},
            {"period": "saturday", "count": 0},
            {"period": "sunday", "count": 1},
        ],
    }


async def test_aggregate_logs_over_time_split_by_actor(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    # top 2 actors over the time window are 1 (3 logs) and 2 (2 logs), actor 3
    # is not part of the top even if it is as active as actor 1 at 12:00
    for emitted_at, extra in (
        ("2026-01-15T10:05:00Z", _actor("1")),
        ("2026-01-15T10:10:00Z", _actor("1")),
        ("2026-01-15T10:20:00Z", _actor("2")),
        ("2026-01-15T11:05:00Z", _actor("2")),
        ("2026-01-15T11:10:00Z", {}),
        ("2026-01-15T12:05:00Z", _actor("1")),
        ("2026-01-15T12:10:00Z", _actor("3")),
    ):
        await repo.create_log_with(log_rw_client, extra, emitted_at=emitted_at)

    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "1_hour", "split_by": "actor", "split_limit": 2},
    )
    assert data == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T10:05:00Z",
        "end": "2026-01-15T12:10:00Z",
        "total_count": 7,
        "timeline": [
            {
                "period": "2026-01-15T10:00:00Z",
                "count": 3,
                "breakdown": [
                    {"actor": {"ref": "1", "name": "User 1"}, "count": 2},
                    {"actor": {"ref": "2", "name": "User 2"}, "count": 1},
                ],
                "other_count": 0,
            },
            {
                "period": "2026-01-15T11:00:00Z",
                "count": 2,
                "breakdown": [{"actor": {"ref": "2", "name": "User 2"}, "count": 1}],
                "other_count": 1,
            },
            {
                "period": "2026-01-15T12:00:00Z",
                "count": 2,
                "breakdown": [{"actor": {"ref": "1", "name": "User 1"}, "count": 1}],
                "other_count": 1,
            },
        ],
    }


async def test_aggregate_logs_over_time_split_by_custom_field_cyclic(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at, status in (
        ("2026-01-15T02:00:00Z", "failure"),
        ("2026-01-16T02:30:00Z", "failure"),
        ("2026-01-16T14:00:00Z", "success"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {"details": [_custom_field("status", status, "enum")]},
            emitted_at=emitted_at,
        )

    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "hour_of_day", "split_by": "details.status"},
    )
    expected_timeline = [
        {"period": period, "count": 0, "breakdown": [], "other_count": 0}
        for period in range(24)
    ]
    expected_timeline[2] = {
        "period": 2,
        "count": 2,
        "breakdown": [{"details.status": "failure", "count": 2}],
        "other_count": 0,
    }
    expected_timeline[14] = {
        "period": 14,
        "count": 1,
        "breakdown": [{"details.status": "success", "count": 1}],
        "other_count": 0,
    }
    assert data == {
        "interval": "hour_of_day",
        "timezone": "UTC",
        "start": "2026-01-15T02:00:00Z",
        "end": "2026-01-16T14:00:00Z",
        "total_count": 3,
        "timeline": expected_timeline,
    }


async def test_aggregate_logs_over_time_count_distinct(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at, actor_ref, action_type in (
        ("2026-01-15T10:05:00Z", "1", "login"),
        ("2026-01-15T10:10:00Z", "2", "login"),
        ("2026-01-15T10:20:00Z", "1", "login"),
        ("2026-01-15T10:30:00Z", "1", "logout"),
        ("2026-01-15T11:30:00Z", "3", "login"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                **_actor(actor_ref),
                **_action(action_type, "authentication"),
            },
            emitted_at=emitted_at,
        )

    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "1_hour", "split_by": "action_type", "count_distinct": "actor"},
    )
    assert data == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T10:05:00Z",
        "end": "2026-01-15T11:30:00Z",
        "total_count": 5,
        "timeline": [
            {
                "period": "2026-01-15T10:00:00Z",
                "count": 4,
                "distinct_count": 2,
                "breakdown": [
                    {"action_type": "login", "count": 3, "distinct_count": 2},
                    {"action_type": "logout", "count": 1, "distinct_count": 1},
                ],
                "other_count": 0,
            },
            {
                "period": "2026-01-15T11:00:00Z",
                "count": 1,
                "distinct_count": 1,
                "breakdown": [
                    {"action_type": "login", "count": 1, "distinct_count": 1}
                ],
                "other_count": 0,
            },
        ],
    }


async def test_aggregate_logs_over_time_string_custom_fields(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at, role, ip in (
        ("2026-01-15T10:05:00Z", "Account Manager", "192.168.1.10"),
        ("2026-01-15T10:10:00Z", "Account Manager", "192.168.1.11"),
        ("2026-01-15T10:20:00Z", "Account Manager", "192.168.1.10"),
        ("2026-01-15T10:30:00Z", "Support Agent", "10.0.0.1"),
        ("2026-01-15T11:30:00Z", "Support Agent", "10.0.0.1"),
    ):
        await repo.create_log_with(
            log_rw_client,
            {
                **_actor("1", extra=[_custom_field("role", role, "string")]),
                "source": [_custom_field("ip", ip, "string")],
            },
            emitted_at=emitted_at,
        )

    assert await call_tool(
        "aggregate_logs_over_time",
        {"interval": "1_hour", "split_by": "actor.role", "count_distinct": "source.ip"},
    ) == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T10:05:00Z",
        "end": "2026-01-15T11:30:00Z",
        "total_count": 5,
        "timeline": [
            {
                "period": "2026-01-15T10:00:00Z",
                "count": 4,
                "distinct_count": 3,
                "breakdown": [
                    {"actor.role": "Account Manager", "count": 3, "distinct_count": 2},
                    {"actor.role": "Support Agent", "count": 1, "distinct_count": 1},
                ],
                "other_count": 0,
            },
            {
                "period": "2026-01-15T11:00:00Z",
                "count": 1,
                "distinct_count": 1,
                "breakdown": [
                    {"actor.role": "Support Agent", "count": 1, "distinct_count": 1}
                ],
                "other_count": 0,
            },
        ],
    }


async def test_aggregate_logs_over_time_with_search_params(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for emitted_at, action_type in (
        ("2026-01-15T10:05:00Z", "login"),
        ("2026-01-15T10:10:00Z", "logout"),
        ("2026-01-15T11:05:00Z", "login"),
    ):
        await repo.create_log_with(
            log_rw_client,
            _action(action_type, "authentication"),
            emitted_at=emitted_at,
        )

    data = await call_tool(
        "aggregate_logs_over_time",
        {"interval": "1_hour", "search_params": {"action_type": "login"}},
    )
    assert data == {
        "interval": "1_hour",
        "timezone": "UTC",
        "start": "2026-01-15T10:05:00Z",
        "end": "2026-01-15T11:05:00Z",
        "total_count": 2,
        "timeline": [
            {"period": "2026-01-15T10:00:00Z", "count": 1},
            {"period": "2026-01-15T11:00:00Z", "count": 1},
        ],
    }


async def test_aggregate_logs_over_time_too_many_periods(
    call_tool: ToolCaller,
):
    one_day = {"since": "2026-01-15T00:00:00Z", "until": "2026-01-15T23:59:59Z"}
    with pytest.raises(ToolError, match="Too many periods.*'15_minutes'"):
        await call_tool(
            "aggregate_logs_over_time",
            {"interval": "5_minutes", "search_params": one_day},
        )


@pytest.mark.parametrize(
    "split_limit,max_periods",
    [
        (1, 200),
        (2, 200),
        (5, 100),
        (10, 50),
    ],
)
async def test_aggregate_logs_over_time_too_many_periods_with_split_by(
    call_tool: ToolCaller,
    split_limit: int,
    max_periods: int,
):
    # the number of breakdown entries (periods x split_limit) is limited
    async def aggregate(period_count: int):
        # the estimated number of periods is (until - since) // interval + 2
        return await call_tool(
            "aggregate_logs_over_time",
            {
                "interval": "1_hour",
                "search_params": {
                    "since": "2026-01-01T00:00:00Z",
                    "until": (
                        datetime.fromisoformat("2026-01-01T00:00:00Z")
                        + timedelta(hours=period_count - 2)
                    ).isoformat(),
                },
                "split_by": "actor",
                "split_limit": split_limit,
            },
        )

    await aggregate(max_periods)
    with pytest.raises(
        ToolError, match=f"Too many periods.*max {max_periods} with split_limit"
    ):
        await aggregate(max_periods + 1)


async def test_aggregate_logs_over_time_too_many_periods_without_time_window(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    # the time window is given by the logs, the number of periods is checked
    # once the aggregation is done
    for emitted_at in ("2026-01-15T00:00:00Z", "2026-01-15T23:59:59Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    with pytest.raises(ToolError, match="Too many periods.*'15_minutes'"):
        await call_tool("aggregate_logs_over_time", {"interval": "5_minutes"})


async def test_aggregate_logs_over_time_too_many_es_buckets(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    # the time window is given by the logs and is too large for the number of
    # ES buckets allowed by ES (search.max_buckets)
    for emitted_at in ("2026-01-01T00:00:00Z", "2026-03-01T00:00:00Z"):
        await repo.create_log_with(log_rw_client, {}, emitted_at=emitted_at)

    with pytest.raises(ToolError, match="Too many periods.*larger interval"):
        await call_tool("aggregate_logs_over_time", {"interval": "1_minute"})


async def test_aggregate_logs_over_time_cyclic_time_window_too_large(
    call_tool: ToolCaller,
):
    with pytest.raises(ToolError, match="Time window is too large"):
        await call_tool(
            "aggregate_logs_over_time",
            {
                "interval": "hour_of_day",
                "search_params": {
                    "since": "2020-01-01T00:00:00Z",
                    "until": "2023-01-01T00:00:00Z",
                },
            },
        )


@pytest.mark.parametrize(
    "params,error",
    [
        ({"interval": "2h"}, None),
        ({"interval": "1_hour", "timezone": "Mars/Olympus"}, "Invalid timezone"),
        ({"interval": "1_hour", "split_by": "unknown"}, "Invalid dimension"),
        ({"interval": "1_hour", "count_distinct": "unknown"}, "Invalid dimension"),
        (
            {"interval": "1_hour", "split_by": "actor", "count_distinct": "actor"},
            "must be different",
        ),
        (
            {"interval": "hour_of_day", "count_distinct": "actor"},
            "count_distinct cannot be used",
        ),
        ({"interval": "1_hour", "split_by": "actor", "split_limit": 11}, None),
        (
            {
                "interval": "1_hour",
                "search_params": {
                    "since": "2026-01-16T00:00:00Z",
                    "until": "2026-01-15T00:00:00Z",
                },
            },
            "since must be before until",
        ),
    ],
)
async def test_aggregate_logs_over_time_invalid_params(
    call_tool: ToolCaller,
    params: dict,
    error: str | None,
):
    with pytest.raises(ToolError, match=error):
        await call_tool("aggregate_logs_over_time", params)


async def test_aggregate_logs_over_time_entity_restricted(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    for entity_path, emitted_at in (
        (["entity_A"], "2026-01-15T10:00:00Z"),  # thursday
        (["entity_A", "entity_A1"], "2026-01-16T10:00:00Z"),  # friday
        (["entity_B"], "2026-01-17T10:00:00Z"),  # saturday
    ):
        await repo.create_log_with_entity_path(
            log_rw_client, entity_path, emitted_at=emitted_at
        )
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "readable_entities": ["entity_A"]}]}}
    )

    assert await ToolCaller(repo, apikey, mcp_client)(
        "aggregate_logs_over_time", {"interval": "day_of_week"}
    ) == {
        "interval": "day_of_week",
        "timezone": "UTC",
        "start": "2026-01-15T10:00:00Z",
        "end": "2026-01-16T10:00:00Z",
        "total_count": 2,
        "timeline": [
            {"period": "monday", "count": 0},
            {"period": "tuesday", "count": 0},
            {"period": "wednesday", "count": 0},
            {"period": "thursday", "count": 1},
            {"period": "friday", "count": 1},
            {"period": "saturday", "count": 0},
            {"period": "sunday", "count": 0},
        ],
    }


async def test_aggregate_logs_over_time_no_permission(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    mcp_client: Client[FastMCPTransport],
):
    apikey = await apikey_builder({})
    with pytest.raises(ToolError, match="permission"):
        await ToolCaller(repo, apikey, mcp_client)(
            "aggregate_logs_over_time", {"interval": "1_hour"}
        )


async def test_describe_repo_empty(
    call_tool: ToolCaller,
):
    assert await call_tool("describe_repo") == {
        "logs": 0,
        "first_log_at": None,
        "last_log_at": None,
        "action_types": {"total": 0, "truncated": False, "items": []},
        "actor_types": [],
        "resource_types": [],
        "logs_without_actor": 0,
        "logs_without_resource": 0,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {"total": 0, "truncated": False, "items": {}},
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def _create_describe_repo_logs(repo: PreparedRepo, client: HttpTestHelper):
    await repo.create_log_with(
        client,
        {
            **_action("login", "auth"),
            **_actor("1"),
            "details": [_custom_field("mfa", True, "boolean")],
        },
        emitted_at="2024-01-01T10:00:00Z",
    )
    await repo.create_log_with(
        client,
        {**_action("login", "auth"), **_actor("2")},
        emitted_at="2024-01-02T10:00:00Z",
    )
    await repo.create_log_with(
        client,
        {
            **_action("view", "doc"),
            **_actor("1"),
            **_resource("a"),
            "source": [_custom_field("ip", "1.2.3.4", "string")],
        },
        emitted_at="2024-01-03T10:00:00Z",
    )


async def test_describe_repo(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await _create_describe_repo_logs(repo, log_rw_client)

    assert await call_tool("describe_repo") == {
        "logs": 3,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": "2024-01-03T10:00:00.000Z",
        "action_types": {
            "total": 2,
            "truncated": False,
            "items": [
                {"name": "login", "category": "auth", "logs": 2},
                {"name": "view", "category": "doc", "logs": 1},
            ],
        },
        "actor_types": [
            {
                "name": "user",
                "logs": 3,
                "distinct_actors": {"count": 2, "approx": False},
            }
        ],
        "resource_types": [
            {
                "name": "doc",
                "logs": 1,
                "distinct_resources": {"count": 1, "approx": False},
            }
        ],
        "logs_without_actor": 0,
        "logs_without_resource": 2,
        "custom_fields": {
            "source": {"total": 1, "truncated": False, "items": {"ip": "string"}},
            "details": {"total": 1, "truncated": False, "items": {"mfa": "boolean"}},
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_repo_with_time_window(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await _create_describe_repo_logs(repo, log_rw_client)

    assert await call_tool(
        "describe_repo",
        {"since": "2024-01-02T00:00:00Z", "until": "2024-01-03T23:59:59Z"},
    ) == {
        "logs": 2,
        "first_log_at": "2024-01-02T10:00:00.000Z",
        "last_log_at": "2024-01-03T10:00:00.000Z",
        "action_types": {
            "total": 2,
            "truncated": False,
            "items": [
                {"name": "login", "category": "auth", "logs": 1},
                {"name": "view", "category": "doc", "logs": 1},
            ],
        },
        "actor_types": [
            {
                "name": "user",
                "logs": 2,
                "distinct_actors": {"count": 2, "approx": False},
            }
        ],
        "resource_types": [
            {
                "name": "doc",
                "logs": 1,
                "distinct_resources": {"count": 1, "approx": False},
            }
        ],
        "logs_without_actor": 0,
        "logs_without_resource": 1,
        "custom_fields": {
            "source": {"total": 1, "truncated": False, "items": {"ip": "string"}},
            "details": {"total": 0, "truncated": False, "items": {}},
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_repo_truncated_action_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await _create_describe_repo_logs(repo, log_rw_client)

    with patch("auditize.mcp.service._MAX_ACTION_TYPES", 1):
        assert await call_tool("describe_repo") == {
            "logs": 3,
            "first_log_at": "2024-01-01T10:00:00.000Z",
            "last_log_at": "2024-01-03T10:00:00.000Z",
            "action_types": {
                "total": 2,
                "truncated": True,
                "items": [{"name": "login", "category": "auth", "logs": 2}],
            },
            "actor_types": [
                {
                    "name": "user",
                    "logs": 3,
                    "distinct_actors": {"count": 2, "approx": False},
                }
            ],
            "resource_types": [
                {
                    "name": "doc",
                    "logs": 1,
                    "distinct_resources": {"count": 1, "approx": False},
                }
            ],
            "logs_without_actor": 0,
            "logs_without_resource": 2,
            "custom_fields": {
                "source": {"total": 1, "truncated": False, "items": {"ip": "string"}},
                "details": {
                    "total": 1,
                    "truncated": False,
                    "items": {"mfa": "boolean"},
                },
                "actor": {"total": 0, "truncated": False, "items": {}},
                "resource": {"total": 0, "truncated": False, "items": {}},
            },
        }


async def test_describe_repo_entity_restricted(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("login"),
            "entity_path": [{"ref": "entity_A", "name": "Entity A"}],
            "details": [_custom_field("visible", "yes", "enum")],
        },
        emitted_at="2024-01-01T10:00:00Z",
    )
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("logout"),
            "entity_path": [{"ref": "entity_B", "name": "Entity B"}],
            "details": [_custom_field("hidden", "yes", "enum")],
        },
        emitted_at="2024-01-02T10:00:00Z",
    )
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "readable_entities": ["entity_A"]}]}}
    )

    assert await ToolCaller(repo, apikey, mcp_client)("describe_repo") == {
        "logs": 1,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": "2024-01-01T10:00:00.000Z",
        "action_types": {
            "total": 1,
            "truncated": False,
            "items": [{"name": "login", "category": "category", "logs": 1}],
        },
        "actor_types": [],
        "resource_types": [],
        "logs_without_actor": 1,
        "logs_without_resource": 1,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {"total": 1, "truncated": False, "items": {"visible": "enum"}},
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_action_unknown(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(log_rw_client, _action("login"))
    with pytest.raises(ToolError, match="Unknown action type 'unknown'"):
        await call_tool("describe_action", {"action_type": "unknown"})


async def test_describe_action_empty_time_window(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("login", "auth"),
            "details": [_custom_field("mfa", True, "boolean")],
        },
        emitted_at="2024-01-01T10:00:00Z",
    )
    assert await call_tool(
        "describe_action", {"action_type": "login", "since": "2025-01-01T00:00:00Z"}
    ) == {
        "action_type": "login",
        "category": "auth",
        "logs": 0,
        "first_log_at": None,
        "last_log_at": None,
        "distinct_actors": {"count": 0, "approx": False},
        "actor_types": [],
        "resource_types": [],
        "logs_without_resource": 0,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {"total": 0, "truncated": False, "items": {}},
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_action(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for i in range(3):
        await repo.create_log_with(
            log_rw_client,
            {
                **_action("view", "doc"),
                **_actor(
                    str(i),
                    "advisor",
                    name=f"Advisor {i}",
                    extra=[_custom_field("region", "north", "enum")],
                ),
                **_resource(str(i)),
                "details": [
                    _custom_field("status", 200 + i, "integer"),
                    _custom_field("scope", "own", "enum"),
                    _custom_field("region", "south", "enum"),
                    _custom_field("at", f"2024-01-0{i + 1}T00:00:00Z", "datetime"),
                    _custom_field("payload", '{"a": 1}', "json"),
                ],
            },
            emitted_at=f"2024-02-0{i + 1}T10:00:00Z",
        )
    # an actor type for which most of the fields are missing
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("view", "doc"),
            **_actor("x", "agent", name="Agent"),
            **_resource("0"),
            "details": [_custom_field("status", 404, "integer")],
        },
        emitted_at="2024-02-04T10:00:00Z",
    )
    # another action whose field must not be listed
    await repo.create_log_with(
        log_rw_client,
        {**_action("login"), "source": [_custom_field("ip", "1.2.3.4", "string")]},
    )

    assert await call_tool("describe_action", {"action_type": "view"}) == {
        "action_type": "view",
        "category": "doc",
        "logs": 4,
        "first_log_at": "2024-02-01T10:00:00.000Z",
        "last_log_at": "2024-02-04T10:00:00.000Z",
        "distinct_actors": {"count": 4, "approx": False},
        "actor_types": [
            {"name": "advisor", "logs": 3},
            {"name": "agent", "logs": 1},
        ],
        "resource_types": [
            {
                "name": "doc",
                "logs": 4,
                "distinct_resources": {"count": 3, "approx": False},
            }
        ],
        "logs_without_resource": 0,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {
                "total": 5,
                "truncated": False,
                "items": {
                    "status": {
                        "type": "integer",
                        "coverage": 1.0,
                        "distinct_values": {"count": 4, "approx": False},
                        "values": {"200": 1, "201": 1, "202": 1, "404": 1},
                        "range": [200, 404],
                    },
                    "at": {
                        "type": "datetime",
                        "coverage": 0.75,
                        "distinct_values": None,
                        "values": None,
                        "range": [
                            "2024-01-01T00:00:00.000Z",
                            "2024-01-03T00:00:00.000Z",
                        ],
                    },
                    "payload": {
                        "type": "json",
                        "coverage": 0.75,
                        "distinct_values": None,
                        "values": None,
                        "range": None,
                    },
                    "region": {
                        "type": "enum",
                        "coverage": 0.75,
                        "distinct_values": {"count": 1, "approx": False},
                        "values": {"south": 3},
                        "range": None,
                    },
                    "scope": {
                        "type": "enum",
                        "coverage": 0.75,
                        "distinct_values": {"count": 1, "approx": False},
                        "values": {"own": 3},
                        "range": None,
                    },
                },
            },
            # same field name as in details, but a distinct field
            "actor": {
                "total": 1,
                "truncated": False,
                "items": {
                    "region": {
                        "type": "enum",
                        "coverage": 0.75,
                        "distinct_values": {"count": 1, "approx": False},
                        "values": {"north": 3},
                        "range": None,
                    },
                },
            },
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


@pytest.mark.parametrize("value_count", [20, 21])
async def test_describe_action_enum_values_limit(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
    value_count: int,
):
    for i in range(value_count):
        await repo.create_log_with(
            log_rw_client,
            {**_action("login"), "details": [_custom_field("code", f"v{i}", "enum")]},
            emitted_at=_emitted_at(i),
        )
    assert await call_tool("describe_action", {"action_type": "login"}) == {
        "action_type": "login",
        "category": "category",
        "logs": value_count,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": f"2024-01-01T10:{value_count - 1:02d}:00.000Z",
        "distinct_actors": {"count": 0, "approx": False},
        "actor_types": [],
        "resource_types": [],
        "logs_without_resource": value_count,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {
                "total": 1,
                "truncated": False,
                "items": {
                    "code": {
                        "type": "enum",
                        "coverage": 1.0,
                        "distinct_values": {"count": value_count, "approx": False},
                        "values": (
                            {f"v{i}": 1 for i in range(value_count)}
                            if value_count <= 20
                            else None
                        ),
                        "range": None,
                    }
                },
            },
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_action_partially_present_boolean_field(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("login"),
            **_actor("1"),
            "details": [_custom_field("mfa", True, "boolean")],
        },
        emitted_at=_emitted_at(0),
    )
    await repo.create_log_with(
        log_rw_client, _action("login"), emitted_at=_emitted_at(1)
    )

    assert await call_tool("describe_action", {"action_type": "login"}) == {
        "action_type": "login",
        "category": "category",
        "logs": 2,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": "2024-01-01T10:01:00.000Z",
        "distinct_actors": {"count": 1, "approx": False},
        "actor_types": [{"name": "user", "logs": 1}],
        "resource_types": [],
        "logs_without_resource": 2,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {
                "total": 1,
                "truncated": False,
                "items": {
                    "mfa": {
                        "type": "boolean",
                        "coverage": 0.5,
                        "distinct_values": {"count": 1, "approx": False},
                        "values": {"true": 1},
                        "range": None,
                    }
                },
            },
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_action_custom_field_with_several_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {**_action("login"), "details": [_custom_field("code", 1, "integer")]},
        emitted_at=_emitted_at(0),
    )
    await repo.create_log_with(
        log_rw_client,
        {**_action("login"), "details": [_custom_field("code", "a", "enum")]},
        emitted_at=_emitted_at(1),
    )

    # only the most recent type of the field is described
    assert await call_tool("describe_action", {"action_type": "login"}) == {
        "action_type": "login",
        "category": "category",
        "logs": 2,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": "2024-01-01T10:01:00.000Z",
        "distinct_actors": {"count": 0, "approx": False},
        "actor_types": [],
        "resource_types": [],
        "logs_without_resource": 2,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {
                "total": 1,
                "truncated": False,
                "items": {
                    "code": {
                        "type": "enum",
                        "coverage": 0.5,
                        "distinct_values": {"count": 1, "approx": False},
                        "values": {"a": 1},
                        "range": None,
                    },
                },
            },
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_action_truncated_custom_fields(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("login"),
            "details": [
                _custom_field("a", "x", "enum"),
                _custom_field("b", "x", "enum"),
            ],
        },
        emitted_at=_emitted_at(0),
    )
    await repo.create_log_with(
        log_rw_client,
        {**_action("login"), "details": [_custom_field("b", "x", "enum")]},
        emitted_at=_emitted_at(1),
    )

    with patch("auditize.mcp.service._MAX_FIELDS_PER_GROUP", 1):
        assert await call_tool("describe_action", {"action_type": "login"}) == {
            "action_type": "login",
            "category": "category",
            "logs": 2,
            "first_log_at": "2024-01-01T10:00:00.000Z",
            "last_log_at": "2024-01-01T10:01:00.000Z",
            "distinct_actors": {"count": 0, "approx": False},
            "actor_types": [],
            "resource_types": [],
            "logs_without_resource": 2,
            "custom_fields": {
                "source": {"total": 0, "truncated": False, "items": {}},
                "details": {
                    "total": 2,
                    "truncated": True,
                    # the field with the highest coverage is kept
                    "items": {
                        "b": {
                            "type": "enum",
                            "coverage": 1.0,
                            "distinct_values": {"count": 1, "approx": False},
                            "values": {"x": 2},
                            "range": None,
                        }
                    },
                },
                "actor": {"total": 0, "truncated": False, "items": {}},
                "resource": {"total": 0, "truncated": False, "items": {}},
            },
        }


@pytest.mark.parametrize("tool_name", ["describe_repo", "describe_action"])
async def test_describe_no_permission(
    tool_name: str,
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    mcp_client: Client[FastMCPTransport],
):
    apikey = await apikey_builder({})
    params = {"action_type": "login"} if tool_name == "describe_action" else {}
    with pytest.raises(ToolError, match="permission"):
        await ToolCaller(repo, apikey, mcp_client)(tool_name, params)


async def test_describe_repo_custom_fields_match_list_fields(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await _create_describe_repo_logs(repo, log_rw_client)
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("view", "doc"),
            **_actor("1", extra=[_custom_field("role", "admin", "enum")]),
            **_resource("a", extra=[_custom_field("size", 12, "integer")]),
        },
    )

    description = await call_tool("describe_repo")
    for group, list_tool in [
        ("source", "list_source_fields"),
        ("details", "list_details_fields"),
        ("actor", "list_actor_extra_fields"),
        ("resource", "list_resource_extra_fields"),
    ]:
        assert await call_tool(list_tool) == {
            "items": [
                {"name": name, "type": type_}
                for name, type_ in description["custom_fields"][group]["items"].items()
            ],
            "next_cursor": None,
        }


async def test_describe_repo_truncated_custom_fields(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("login"),
            "details": [
                _custom_field("a", "x", "enum"),
                _custom_field("b", "x", "enum"),
            ],
        },
        emitted_at=_emitted_at(0),
    )
    await repo.create_log_with(
        log_rw_client,
        {**_action("login"), "details": [_custom_field("b", "x", "enum")]},
        emitted_at=_emitted_at(1),
    )

    with patch("auditize.mcp.service._MAX_FIELDS_PER_GROUP", 1):
        assert await call_tool("describe_repo") == {
            "logs": 2,
            "first_log_at": "2024-01-01T10:00:00.000Z",
            "last_log_at": "2024-01-01T10:01:00.000Z",
            "action_types": {
                "total": 1,
                "truncated": False,
                "items": [{"name": "login", "category": "category", "logs": 2}],
            },
            "actor_types": [],
            "resource_types": [],
            "logs_without_actor": 2,
            "logs_without_resource": 2,
            "custom_fields": {
                "source": {"total": 0, "truncated": False, "items": {}},
                # the most frequent field is kept
                "details": {"total": 2, "truncated": True, "items": {"b": "enum"}},
                "actor": {"total": 0, "truncated": False, "items": {}},
                "resource": {"total": 0, "truncated": False, "items": {}},
            },
        }


async def test_describe_repo_custom_field_with_several_types(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await repo.create_log_with(
        log_rw_client,
        {**_action("login"), "details": [_custom_field("code", 1, "integer")]},
        emitted_at=_emitted_at(0),
    )
    await repo.create_log_with(
        log_rw_client,
        {**_action("login"), "details": [_custom_field("code", "a", "enum")]},
        emitted_at=_emitted_at(1),
    )

    assert await call_tool("describe_repo") == {
        "logs": 2,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": "2024-01-01T10:01:00.000Z",
        "action_types": {
            "total": 1,
            "truncated": False,
            "items": [{"name": "login", "category": "category", "logs": 2}],
        },
        "actor_types": [],
        "resource_types": [],
        "logs_without_actor": 2,
        "logs_without_resource": 2,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            # only the most recent type of the field is given
            "details": {"total": 1, "truncated": False, "items": {"code": "enum"}},
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_repo_approximate_distinct_counts(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    await _create_describe_repo_logs(repo, log_rw_client)

    with patch("auditize.mcp.service._CARDINALITY_PRECISION_THRESHOLD", 1):
        assert await call_tool("describe_repo") == {
            "logs": 3,
            "first_log_at": "2024-01-01T10:00:00.000Z",
            "last_log_at": "2024-01-03T10:00:00.000Z",
            "action_types": {
                "total": 2,
                "truncated": False,
                "items": [
                    {"name": "login", "category": "auth", "logs": 2},
                    {"name": "view", "category": "doc", "logs": 1},
                ],
            },
            "actor_types": [
                {
                    "name": "user",
                    "logs": 3,
                    # above the precision threshold
                    "distinct_actors": {"count": 2, "approx": True},
                }
            ],
            "resource_types": [
                {
                    "name": "doc",
                    "logs": 1,
                    # not above the precision threshold
                    "distinct_resources": {"count": 1, "approx": False},
                }
            ],
            "logs_without_actor": 0,
            "logs_without_resource": 2,
            "custom_fields": {
                "source": {"total": 1, "truncated": False, "items": {"ip": "string"}},
                "details": {
                    "total": 1,
                    "truncated": False,
                    "items": {"mfa": "boolean"},
                },
                "actor": {"total": 0, "truncated": False, "items": {}},
                "resource": {"total": 0, "truncated": False, "items": {}},
            },
        }


async def test_describe_action_entity_restricted(
    repo: PreparedRepo,
    apikey_builder: ApikeyBuilder,
    log_rw_client: HttpTestHelper,
    mcp_client: Client[FastMCPTransport],
):
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("login"),
            **_actor("1"),
            "entity_path": [{"ref": "entity_A", "name": "Entity A"}],
            "details": [_custom_field("mfa", True, "boolean")],
        },
        emitted_at=_emitted_at(0),
    )
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("login"),
            **_actor("2"),
            "entity_path": [{"ref": "entity_B", "name": "Entity B"}],
            "details": [
                _custom_field("mfa", False, "boolean"),
                _custom_field("method", "otp", "enum"),
            ],
        },
        emitted_at=_emitted_at(1),
    )
    await repo.create_log_with(
        log_rw_client,
        {
            **_action("logout"),
            "entity_path": [{"ref": "entity_B", "name": "Entity B"}],
        },
        emitted_at=_emitted_at(2),
    )
    apikey = await apikey_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "readable_entities": ["entity_A"]}]}}
    )

    # an action type only existing in a non readable entity is unknown
    with pytest.raises(ToolError, match="Unknown action type 'logout'"):
        await ToolCaller(repo, apikey, mcp_client)(
            "describe_action", {"action_type": "logout"}
        )

    # logs of non readable entities are not taken into account
    assert await ToolCaller(repo, apikey, mcp_client)(
        "describe_action", {"action_type": "login"}
    ) == {
        "action_type": "login",
        "category": "category",
        "logs": 1,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": "2024-01-01T10:00:00.000Z",
        "distinct_actors": {"count": 1, "approx": False},
        "actor_types": [{"name": "user", "logs": 1}],
        "resource_types": [],
        "logs_without_resource": 1,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {
                "total": 1,
                "truncated": False,
                "items": {
                    "mfa": {
                        "type": "boolean",
                        "coverage": 1.0,
                        "distinct_values": {"count": 1, "approx": False},
                        "values": {"true": 1},
                        "range": None,
                    }
                },
            },
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }


async def test_describe_action_float_and_string_fields(
    repo: PreparedRepo,
    log_rw_client: HttpTestHelper,
    call_tool: ToolCaller,
):
    for i, (amount, label) in enumerate([(1.5, "first"), (2.5, "second")]):
        await repo.create_log_with(
            log_rw_client,
            {
                **_action("login"),
                "details": [
                    _custom_field("amount", amount, "float"),
                    _custom_field("label", label, "string"),
                ],
            },
            emitted_at=_emitted_at(i),
        )

    assert await call_tool("describe_action", {"action_type": "login"}) == {
        "action_type": "login",
        "category": "category",
        "logs": 2,
        "first_log_at": "2024-01-01T10:00:00.000Z",
        "last_log_at": "2024-01-01T10:01:00.000Z",
        "distinct_actors": {"count": 0, "approx": False},
        "actor_types": [],
        "resource_types": [],
        "logs_without_resource": 2,
        "custom_fields": {
            "source": {"total": 0, "truncated": False, "items": {}},
            "details": {
                "total": 2,
                "truncated": False,
                "items": {
                    "amount": {
                        "type": "float",
                        "coverage": 1.0,
                        "distinct_values": {"count": 2, "approx": False},
                        "values": {"1.5": 1, "2.5": 1},
                        "range": [1.5, 2.5],
                    },
                    # string fields are full-text fields, only their coverage is given
                    "label": {
                        "type": "string",
                        "coverage": 1.0,
                        "distinct_values": None,
                        "values": None,
                        "range": None,
                    },
                },
            },
            "actor": {"total": 0, "truncated": False, "items": {}},
            "resource": {"total": 0, "truncated": False, "items": {}},
        },
    }
