from datetime import datetime
from bson import ObjectId
import base64

import pytest
import callee
from icecream import ic

from auditize.common.mongo import RepoDatabase
from auditize.logs.service import (
    consolidate_log_event, consolidate_log_actor, consolidate_log_resource,
    consolidate_log_tags, consolidate_log_node_path
)
from auditize.logs.models import Log

from helpers import (
    UNKNOWN_LOG_ID, RepoTest,
    do_test_page_pagination_common_scenarios,
    do_test_page_pagination_empty_data,
    make_log_data, make_expected_log_data_for_api, assert_create_log, prepare_log,
    alter_log_saved_at
)
from helpers.http import HttpTestHelper

pytestmark = pytest.mark.anyio


async def assert_db_log(db: RepoDatabase, log_id, expected):
    expected = {**make_expected_log_data_for_api(expected), "saved_at": callee.IsA(datetime)}
    db_log = await db.logs.find_one({"_id": ObjectId(log_id)}, {"_id": 0})
    ic(db_log)
    assert db_log == expected


async def test_create_log_minimal_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    resp = await assert_create_log(client, repo.id, log)
    await assert_db_log(repo.db, resp.json()["id"], log)


async def test_create_log_all_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data({
        "source": {
            "ip": "1.1.1.1",
            "user_agent": "Mozilla/5.0"
        },
        "actor": {
            "type": "user",
            "id": "user:123",
            "name": "User 123",
            "extra": {
                "role": "admin"
            }
        },
        "resource": {
            "type": "module",
            "id": "core",
            "name": "Core Module",
            "extra": {
                "creator": "xyz"
            }
        },
        "details": {
            "more_details": {
                "some_key": "some_value"
            },
            "other_details": {
                "other_key": "other_value"
            }
        },
        "tags": [
            {
                "id": "simple_tag",
            },
            {
                "id": "rich_tag:1",
                "category": "rich_tag",
                "name": "Rich tag"
            }
        ],
    })

    resp = await assert_create_log(client, repo.id, log)
    await assert_db_log(repo.db, resp.json()["id"], log)


async def test_create_log_missing_event_name(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    del log["event"]["name"]
    await assert_create_log(client, repo.id, log, expected_status_code=422)


async def test_create_log_invalid_rich_tag(client: HttpTestHelper, repo: RepoTest):
    invalid_tags = (
        {"id": "some_tag", "category": "rich_tag"},
        {"id": "some_other_tag", "name": "Rich tag"}
    )

    for invalid_tag in invalid_tags:
        await assert_create_log(
            client, repo.id, make_log_data({"tags": [invalid_tag]}), expected_status_code=422
        )


async def test_add_attachment_text_and_minimal_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    log_id = await prepare_log(client, repo.id, log)

    await client.assert_post(
        f"/repos/{repo.id}/logs/{log_id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
        expected_status_code=204
    )
    await assert_db_log(
        repo.db, log_id, {
            **log,
            "attachments": [
                {
                    "name": "test.txt",
                    "type": "text",
                    "mime_type": "text/plain",
                    "data": b"test data"
                }
            ]
        }
    )


async def test_add_attachment_binary_and_all_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    log_id = await prepare_log(client, repo.id, log)

    # some random data generated with /dev/urandom:
    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await client.assert_post(
        f"/repos/{repo.id}/logs/{log_id}/attachments",
        files={"file": ("file.bin", data)},
        data={"type": "binary", "name": "test_file.bin", "mime_type": "application/octet-stream"},
        expected_status_code=204
    )
    await assert_db_log(
        repo.db, log_id, {
            **log,
            "attachments": [
                {
                    "name": "test_file.bin",
                    "type": "binary",
                    "mime_type": "application/octet-stream",
                    "data": data
                }
            ]
        }
    )


async def test_get_log_minimal_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    log_id = await prepare_log(client, repo.id, log)

    await client.assert_get(
        f"/repos/{repo.id}/logs/{log_id}",
        expected_json=make_expected_log_data_for_api({
            **log,
            "id": log_id
        })
    )


async def test_get_log_all_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data({
        "source": {
            "ip": "1.1.1.1",
            "user_agent": "Mozilla/5.0"
        },
        "actor": {
            "type": "user",
            "id": "user:123",
            "name": "User 123",
            "extra": {
                "role": "admin"
            }
        },
        "resource": {
            "type": "module",
            "id": "core",
            "name": "Core Module",
            "extra": {
                "creator": "xyz"
            }
        },
        "details": {
            "more_details": {
                "some_key": "some_value"
            },
            "other_details": {
                "other_key": "other_value"
            }
        },
        "tags": [
            {
                "id": "simple_tag",
            },
            {
                "id": "rich_tag:1",
                "category": "rich_tag",
                "name": "Rich tag"
            }
        ],
    })

    log_id = await prepare_log(client, repo.id, log)

    await client.assert_get(
        f"/repos/{repo.id}/logs/{log_id}",
        expected_json=make_expected_log_data_for_api({
            **log,
            "id": log_id
        })
    )


async def test_get_log_not_found(client: HttpTestHelper, repo: RepoTest):
    await client.assert_get(
        f"/repos/{repo.id}/logs/{UNKNOWN_LOG_ID}", expected_status_code=404
    )


async def test_get_log_attachment_text_and_minimal_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    log_id = await prepare_log(client, repo.id, log)

    await client.assert_post(
        f"/repos/{repo.id}/logs/{log_id}/attachments",
        files={"file": ("file.txt", "test data")},
        data={"type": "text file"},
        expected_status_code=204
    )

    resp = await client.assert_get(f"/repos/{repo.id}/logs/{log_id}/attachments/0")
    assert resp.headers["Content-Disposition"] == "attachment; filename=file.txt"
    assert resp.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert resp.content == b"test data"


async def test_get_log_attachment_binary_and_all_fields(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    log_id = await prepare_log(client, repo.id, log)

    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await client.assert_post(
        f"/repos/{repo.id}/logs/{log_id}/attachments",
        files={"file": ("file.bin", data)},
        data={"type": "binary", "name": "test_file.bin", "mime_type": "image/jpeg"},
        expected_status_code=204
    )

    resp = await client.assert_get(f"/repos/{repo.id}/logs/{log_id}/attachments/0")
    assert resp.headers["Content-Disposition"] == "attachment; filename=test_file.bin"
    assert resp.headers["Content-Type"] == "image/jpeg"
    assert resp.content == data


async def test_get_log_attachment_not_found_log_id(client: HttpTestHelper, repo: RepoTest):
    await client.assert_get(
        f"/repos/{repo.id}/logs/{UNKNOWN_LOG_ID}/attachments/0", expected_status_code=404
    )


async def test_get_log_attachment_not_found_attachment_idx(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    log_id = await prepare_log(client, repo.id, log)

    await client.assert_get(f"/repos/{repo.id}/logs/{log_id}/attachments/0", expected_status_code=404)


async def test_get_logs(client: HttpTestHelper, repo: RepoTest):
    log1 = make_log_data()
    log2 = make_log_data()
    log1_id = await prepare_log(client, repo.id, log1)
    log2_id = await prepare_log(client, repo.id, log2)

    await client.assert_get(
        f"/repos/{repo.id}/logs",
        expected_json={
            "data": [
                make_expected_log_data_for_api({
                    **log2,
                    "id": log2_id
                }),
                make_expected_log_data_for_api({
                    **log1,
                    "id": log1_id
                })
            ],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def test_get_logs_limit(client: HttpTestHelper, repo: RepoTest):
    log1 = make_log_data()
    log2 = make_log_data()
    await prepare_log(client, repo.id, log1)
    log2_id = await prepare_log(client, repo.id, log2)

    await client.assert_get(
        f"/repos/{repo.id}/logs?limit=1",
        expected_json={
            "data": [
                make_expected_log_data_for_api({
                    **log2,
                    "id": log2_id
                })
            ],
            "pagination": {
                "next_cursor": callee.IsA(str)
            }
        }
    )


async def test_get_logs_limit_and_cursor(client: HttpTestHelper, repo: RepoTest):
    logs = []
    log_ids = []
    for _ in range(10):
        log = make_log_data()
        logs.append(log)
        log_id = await prepare_log(client, repo.id, log)
        log_ids.append(log_id)

    # first step, get 5 logs and check the next_cursor
    resp = await client.assert_get(
        f"/repos/{repo.id}/logs?limit=5",
        expected_json={
            "data": [
                make_expected_log_data_for_api({**log, "id": log_id})
                for log, log_id in zip(reversed(logs[-5:]), reversed(log_ids[-5:]))
            ],
            "pagination": {
                "next_cursor": callee.IsA(str)
            }
        }
    )
    next_cursor = resp.json()["pagination"]["next_cursor"]

    # second step, get the next 5 logs using the next_cursor from the previous response and check next_cursor is None
    await client.assert_get(
        f"/repos/{repo.id}/logs?limit=5&cursor={next_cursor}",
        expected_json={
            "data": [
                make_expected_log_data_for_api({**log, "id": log_id})
                for log, log_id in zip(reversed(logs[:5]), reversed(log_ids[:5]))
            ],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def _test_get_logs_filter(client: HttpTestHelper, repo_id: str, func, params):
    log1 = make_log_data()
    await prepare_log(client, repo_id, log1)
    log2 = make_log_data()
    func(log2)
    log2_id = await prepare_log(client, repo_id, log2)

    await client.assert_get(
        f"/repos/{repo_id}/logs", params=params,
        expected_json={
            "data": [
                make_expected_log_data_for_api({
                    **log2,
                    "id": log2_id
                })
            ],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def test_get_logs_filter_event_name(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["event"]["name"] = "find_me"

    await _test_get_logs_filter(client, repo.id, func, {"event_name": "find_me"})


async def test_get_logs_filter_event_category(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["event"]["category"] = "find_me"

    await _test_get_logs_filter(client, repo.id, func, {"event_category": "find_me"})


async def test_get_logs_filter_actor_type(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["actor"] = {
            "type": "find_me",
            "id": "user:123",
            "name": "User 123"
        }

    await _test_get_logs_filter(client, repo.id, func, {"actor_type": "find_me"})


async def test_get_logs_filter_actor_name(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["actor"] = {
            "type": "user",
            "id": "user:123",
            "name": "find_me"
        }

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(client, repo.id, func, {"actor_name": "FIND"})


async def test_get_logs_filter_resource_type(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["resource"] = {
            "type": "find_me",
            "id": "core",
            "name": "Core Module"
        }

    await _test_get_logs_filter(client, repo.id, func, {"resource_type": "find_me"})


async def test_get_logs_filter_resource_name(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["resource"] = {
            "type": "module",
            "id": "core",
            "name": "find_me"
        }

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(client, repo.id, func, {"resource_name": "FIND"})


async def test_get_logs_filter_tag_category(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "rich_tag:1", "category": "find_me", "name": "Rich tag"}
        ]

    await _test_get_logs_filter(client, repo.id, func, {"tag_category": "find_me"})


async def test_get_logs_filter_tag_name(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "rich_tag:1", "category": "rich_tag", "name": "find_me"}
        ]

    # filter on tag_name is substring and case-insensitive
    await _test_get_logs_filter(client, repo.id, func, {"tag_name": "FIND"})


async def test_get_logs_filter_tag_id(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "find_me", "category": "rich_tag", "name": "Rich tag"}
        ]

    await _test_get_logs_filter(client, repo.id, func, {"tag_id": "find_me"})


async def test_get_logs_filter_node_id_exact_node(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["node_path"] = [
            {"id": "find_me:1", "name": "Customer 1"},
            {"id": "find_me:2", "name": "Customer 2"}
        ]

    await _test_get_logs_filter(client, repo.id, func, {"node_id": "find_me:2"})


async def test_get_logs_filter_node_id_ascendant_node(client: HttpTestHelper, repo: RepoTest):
    def func(log):
        log["node_path"] = [
            {"id": "find_me:1", "name": "Customer 1"},
            {"id": "find_me:2", "name": "Customer 2"}
        ]

    await _test_get_logs_filter(client, repo.id, func, {"node_id": "find_me:1"})


async def test_get_logs_filter_since(client: HttpTestHelper, repo: RepoTest):
    log1 = make_log_data()
    log1_id = await prepare_log(client, repo.id, log1)
    alter_log_saved_at(repo.db, log1_id, datetime.fromisoformat("2024-01-01T00:00:00Z"))
    log2 = make_log_data()
    log2_id = await prepare_log(client, repo.id, log2)
    alter_log_saved_at(repo.db, log2_id, datetime.fromisoformat("2024-01-02T00:00:00Z"))

    await client.assert_get(
        f"/repos/{repo.id}/logs", params={"since": "2024-01-01T12:00:00Z"},
        expected_json={
            "data": [
                make_expected_log_data_for_api({
                    **log2,
                    "id": log2_id
                })
            ],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def test_get_logs_filter_until(client: HttpTestHelper, repo: RepoTest):
    log1 = make_log_data()
    log1_id = await prepare_log(client, repo.id, log1)
    alter_log_saved_at(repo.db, log1_id, datetime.fromisoformat("2024-01-01T00:00:00Z"))
    log2 = make_log_data()
    log2_id = await prepare_log(client, repo.id, log2)
    alter_log_saved_at(repo.db, log2_id, datetime.fromisoformat("2024-01-02T00:00:00Z"))

    await client.assert_get(
        f"/repos/{repo.id}/logs", params={"until": "2024-01-01T12:00:00Z"},
        expected_json={
            "data": [
                make_expected_log_data_for_api({
                    **log1,
                    "id": log1_id
                })
            ],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def test_get_logs_filter_until_milliseconds(client: HttpTestHelper, repo: RepoTest):
    log1 = make_log_data()
    log1_id = await prepare_log(client, repo.id, log1)
    alter_log_saved_at(repo.db, log1_id, datetime.fromisoformat("2023-12-31T23:59:59.500Z"))
    log2 = make_log_data()
    log2_id = await prepare_log(client, repo.id, log2)
    alter_log_saved_at(repo.db, log2_id, datetime.fromisoformat("2024-01-01T00:00:00Z"))

    await client.assert_get(
        f"/repos/{repo.id}/logs", params={"until": "2023-12-31T23:59:59Z"},
        expected_json={
            "data": [
                make_expected_log_data_for_api({
                    **log1,
                    "id": log1_id
                })
            ],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def test_get_logs_filter_between_since_and_until(client: HttpTestHelper, repo: RepoTest):
    log1 = make_log_data()
    log1_id = await prepare_log(client, repo.id, log1)
    alter_log_saved_at(repo.db, log1_id, datetime.fromisoformat("2024-01-01T00:00:00Z"))
    log2 = make_log_data()
    log2_id = await prepare_log(client, repo.id, log2)
    alter_log_saved_at(repo.db, log2_id, datetime.fromisoformat("2024-01-02T00:00:00Z"))
    log3 = make_log_data()
    log3_id = await prepare_log(client, repo.id, log3)
    alter_log_saved_at(repo.db, log3_id, datetime.fromisoformat("2024-01-03T00:00:00Z"))

    resp = await client.assert_get(
        f"/repos/{repo.id}/logs", params={"since": "2024-01-01T12:00:00Z", "until": "2024-01-02T12:00:00Z"}
    )
    assert resp.json() == {
        "data": [
            make_expected_log_data_for_api({
                **log2,
                "id": log2_id
            })
        ],
        "pagination": {
            "next_cursor": None
        }
    }


async def test_get_logs_filter_multiple_criteria(client: HttpTestHelper, repo: RepoTest):
    log1 = make_log_data()
    log1["event"]["name"] = "find_me:event_name"
    await prepare_log(client, repo.id, log1)

    log2 = make_log_data()
    log2["event"]["category"] = "find_me:event_category"
    await prepare_log(client, repo.id, log2)

    log3 = make_log_data()
    log3["event"] = {"name": "find_me:event_name", "category": "find_me:event_category"}
    log3_id = await prepare_log(client, repo.id, log3)

    await client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"event_name": "find_me:event_name", "event_category": "find_me:event_category"},
        expected_json={
            "data": [
                make_expected_log_data_for_api({
                    **log3,
                    "id": log3_id
                })
            ],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def test_get_logs_empty_string_filter_params(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    log_id = await prepare_log(client, repo.id, log)

    resp = await client.assert_get(f"/repos/{repo.id}/logs", params={
        "event_name": "", "event_category": "",
        "actor_type": "", "actor_name": "",
        "resource_type": "", "resource_name": "",
        "tag_category": "", "tag_name": "", "tag_id": "",
        "node_id": "",
        "since": "", "until": ""
    })
    assert resp.json() == {
        "data": [
            make_expected_log_data_for_api({
                **log,
                "id": log_id
            })
        ],
        "pagination": {
            "next_cursor": None
        }
    }


async def test_get_logs_filter_no_result(client: HttpTestHelper, repo: RepoTest):
    log = make_log_data()
    await prepare_log(client, repo.id, log)

    await client.assert_get(
        f"/repos/{repo.id}/logs", params={"event_name": "not to be found"},
        expected_json={
            "data": [],
            "pagination": {
                "next_cursor": None
            }
        }
    )


async def test_get_log_event_categories(client: HttpTestHelper, repo: RepoTest):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_event(repo.db, Log.Event(category=f"category_{i}", name=f"name_{i}"))
        await consolidate_log_event(repo.db, Log.Event(category=f"category_{i}", name=f"name_{i + 10}"))

    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/event-categories", [f"category_{i}" for i in range(5)]
    )


async def test_get_log_event_categories_empty(client: HttpTestHelper, repo: RepoTest):
    await do_test_page_pagination_empty_data(client, f"/repos/{repo.id}/logs/event-categories")


async def test_get_log_event_names(client: HttpTestHelper, repo: RepoTest):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_event(repo.db, Log.Event(category=f"category_{i}", name=f"name_{i}"))
        await consolidate_log_event(repo.db, Log.Event(category=f"category_{i + 10}", name=f"name_{i}"))

    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/events", [f"name_{i}" for i in range(5)]
    )

    # test category parameter
    await client.assert_get(
        f"/repos/{repo.id}/logs/events?category=category_2",
        expected_json={
            "data": [
                f"name_{2}"
            ],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 1,
                "total_pages": 1
            }
        }
    )


async def test_get_log_event_names_empty(client: HttpTestHelper, repo: RepoTest):
    await do_test_page_pagination_empty_data(client, f"/repos/{repo.id}/logs/events")


async def test_get_log_actor_types(client: HttpTestHelper, repo: RepoTest):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_actor(repo.db, Log.Actor(type=f"type_{i}", id=f"id_{i}", name=f"name_{i}"))

    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/actor-types", [f"type_{i}" for i in range(5)]
    )


async def test_get_log_actor_types_empty(client: HttpTestHelper, repo: RepoTest):
    await do_test_page_pagination_empty_data(client, f"/repos/{repo.id}/logs/actor-types")


async def test_get_log_resource_types(client: HttpTestHelper, repo: RepoTest):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_resource(repo.db, Log.Resource(type=f"type_{i}", id=f"id_{i}", name=f"name_{i}"))

    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/resource-types", [f"type_{i}" for i in range(5)]
    )


async def test_get_log_resource_types_empty(client: HttpTestHelper, repo: RepoTest):
    await do_test_page_pagination_empty_data(client, f"/repos/{repo.id}/logs/resource-types")


async def test_get_log_tag_categories(client: HttpTestHelper, repo: RepoTest):
    for i in reversed(range(5)):
        await consolidate_log_tags(repo.db, [Log.Tag(id=f"tag_{i}", category=f"category_{i}", name=f"name_{i}")])
    await consolidate_log_tags(repo.db, [Log.Tag(id="simple_tag")])  # no category, it must not be returned

    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/tag-categories", [f"category_{i}" for i in range(5)]
    )


async def test_get_log_tag_categories_empty(client: HttpTestHelper, repo: RepoTest):
    await do_test_page_pagination_empty_data(client, f"/repos/{repo.id}/logs/tag-categories")


async def test_get_log_nodes_without_filters(client: HttpTestHelper, repo: RepoTest):
    for i in range(4):
        await consolidate_log_node_path(
            repo.db, [Log.Node(id=f"customer", name=f"Customer"), Log.Node(id=f"entity:{i}", name=f"Entity {i}")]
        )

    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/nodes",
        [{"id": "customer", "name": "Customer", "parent_node_id": None, "has_children": True}] +
        [{"id": f"entity:{i}", "name": f"Entity {i}", "parent_node_id": "customer", "has_children": False}
         for i in range(4)]
    )


async def test_get_log_nodes_with_filters(client: HttpTestHelper, repo: RepoTest):
    for i in range(5):
        for j in "a", "b", "c", "d", "e":
            await consolidate_log_node_path(
                repo.db, [
                    Log.Node(id=f"customer:{i}", name=f"Customer {i}"),
                    Log.Node(id=f"entity:{i}-{j}", name=f"Entity {j}")
                ]
            )

    # test top-level nodes
    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/nodes?root=true",
        [{"id": f"customer:{i}", "name": f"Customer {i}", "parent_node_id": None, "has_children": True}
         for i in range(5)]
    )

    # test non-top-level nodes
    await do_test_page_pagination_common_scenarios(
        client, f"/repos/{repo.id}/logs/nodes?parent_node_id=customer:2",
        [{"id": f"entity:2-{j}", "name": f"Entity {j}", "parent_node_id": "customer:2", "has_children": False}
         for j in ("a", "b", "c", "d", "e")]
    )


async def test_get_log_nodes_empty(client: HttpTestHelper, repo: RepoTest):
    await do_test_page_pagination_empty_data(client, f"/repos/{repo.id}/logs/nodes")


async def test_get_log_node(client: HttpTestHelper, repo: RepoTest):
    await consolidate_log_node_path(
        repo.db, [Log.Node(id="customer", name="Customer"), Log.Node(id="entity", name="Entity")]
    )

    await client.assert_get(
        f"/repos/{repo.id}/logs/nodes/customer",
        expected_json={
            "id": "customer",
            "name": "Customer",
            "parent_node_id": None,
            "has_children": True
        }
    )

    await client.assert_get(
        f"/repos/{repo.id}/logs/nodes/entity",
        expected_json={
            "id": "entity",
            "name": "Entity",
            "parent_node_id": "customer",
            "has_children": False
        }
    )

