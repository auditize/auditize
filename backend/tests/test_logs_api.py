import time
import datetime
from bson import ObjectId
import base64

import pytest
import callee
from httpx import AsyncClient
from icecream import ic

from auditize.common.mongo import Database
from auditize.logs.service import (consolidate_log_event, consolidate_log_actor, consolidate_log_resource,
                                   consolidate_log_tags, consolidate_log_node_path)
from auditize.logs.models import Log


pytestmark = pytest.mark.anyio


# a valid ObjectId, but not existing in the database
UNKNOWN_LOG_ID = "65fab045f097fe0b9b664c99"


def make_log_data(extra=None) -> dict:
    """
    By default, the log data is minimal viable.
    """

    extra = extra or {}

    return {
        "event": {
            "name": "user_login",
            "category": "authentication",
        },
        "node_path": [
            {
                "id": "1",
                "name": "Customer 1"
            }
        ],
        **extra
    }


def make_expected_log_data_for_api(actual):
    expected = {
        "source": {},
        "actor": None,
        "resource": None,
        "details": {},
        "tags": [],
        "attachments": [],
        **actual,
        "saved_at": callee.Regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
    }
    for tag in expected["tags"]:
        tag.setdefault("category", None)
        tag.setdefault("name", None)
    if expected["actor"]:
        expected["actor"].setdefault("extra", {})
    if expected["resource"]:
        expected["resource"].setdefault("extra", {})
    return expected


async def assert_request(method: str, client: AsyncClient, path, *, params=None, json=None, files=None, data=None,
                         expected_status_code=200):
    ic(json, files, data)
    resp = await client.request(method, path, params=params, json=json, files=files, data=data)
    ic(resp.text)
    assert resp.status_code == expected_status_code
    return resp


async def assert_post(client: AsyncClient, path, *, json=None, files=None, data=None, expected_status_code=200):
    return await assert_request(
        "POST", client, path,
        json=json, files=files, data=data, expected_status_code=expected_status_code
    )


async def assert_get(client: AsyncClient, path, *, params=None, expected_status_code=200):
    return await assert_request("GET", client, path, params=params, expected_status_code=expected_status_code)


async def assert_create_log(client: AsyncClient, log: dict, expected_status_code=201):
    resp = await assert_post(client, "/logs", json=log, expected_status_code=expected_status_code)
    if expected_status_code == 201:
        assert "id" in resp.json()
    return resp


async def prepare_log(client: AsyncClient, log: dict):
    resp = await assert_create_log(client, log)
    return resp.json()["id"]


async def assert_db_log(db: Database, log_id, expected):
    expected = {**make_expected_log_data_for_api(expected), "saved_at": callee.IsA(datetime.datetime)}
    db_log = await db.logs.find_one({"_id": ObjectId(log_id)}, {"_id": 0})
    ic(db_log)
    assert db_log == expected


async def test_create_log_minimal_fields(client: AsyncClient, db: Database):
    log = make_log_data()
    resp = await assert_create_log(client, log)
    await assert_db_log(db, resp.json()["id"], log)


async def test_create_log_all_fields(client: AsyncClient, db: Database):
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

    resp = await assert_create_log(client, log)
    await assert_db_log(db, resp.json()["id"], log)


async def test_create_log_missing_event_name(client: AsyncClient, db: Database):
    log = make_log_data()
    del log["event"]["name"]
    await assert_create_log(client, log, expected_status_code=422)


async def test_create_log_invalid_rich_tag(client: AsyncClient, db: Database):
    invalid_tags = (
        {"id": "some_tag", "category": "rich_tag"},
        {"id": "some_other_tag", "name": "Rich tag"}
    )

    for invalid_tag in invalid_tags:
        await assert_create_log(client, make_log_data({"tags": [invalid_tag]}), expected_status_code=422)


async def test_add_attachment_text_and_minimal_fields(client: AsyncClient, db: Database):
    log = make_log_data()
    log_id = await prepare_log(client, log)

    await assert_post(
        client,
        f"/logs/{log_id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
        expected_status_code=204
    )
    await assert_db_log(
        db, log_id, {
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


async def test_add_attachment_binary_and_all_fields(client: AsyncClient, db: Database):
    log = make_log_data()
    log_id = await prepare_log(client, log)

    # some random data generated with /dev/urandom:
    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await assert_post(
        client,
        f"/logs/{log_id}/attachments",
        files={"file": ("file.bin", data)},
        data={"type": "binary", "name": "test_file.bin", "mime_type": "application/octet-stream"},
        expected_status_code=204
    )
    await assert_db_log(
        db, log_id, {
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


async def test_get_log_minimal_fields(client: AsyncClient, db: Database):
    log = make_log_data()
    log_id = await prepare_log(client, log)

    resp = await assert_get(client, f"/logs/{log_id}")
    assert resp.json() == make_expected_log_data_for_api({
        **log,
        "id": log_id
    })


async def test_get_log_all_fields(client: AsyncClient, db: Database):
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

    log_id = await prepare_log(client, log)

    resp = await assert_get(client, f"/logs/{log_id}")
    assert resp.json() == make_expected_log_data_for_api({
        **log,
        "id": log_id
    })


async def test_get_log_not_found(client: AsyncClient, db: Database):
    await assert_get(client, f"/logs/{UNKNOWN_LOG_ID}", expected_status_code=404)


async def test_get_log_attachment_text_and_minimal_fields(client: AsyncClient, db: Database):
    log = make_log_data()
    log_id = await prepare_log(client, log)

    await assert_post(
        client,
        f"/logs/{log_id}/attachments",
        files={"file": ("file.txt", "test data")},
        data={"type": "text file"},
        expected_status_code=204
    )

    resp = await assert_get(client, f"/logs/{log_id}/attachments/0")
    assert resp.headers["Content-Disposition"] == "attachment; filename=file.txt"
    assert resp.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert resp.content == b"test data"


async def test_get_log_attachment_binary_and_all_fields(client: AsyncClient, db: Database):
    log = make_log_data()
    log_id = await prepare_log(client, log)

    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await assert_post(
        client,
        f"/logs/{log_id}/attachments",
        files={"file": ("file.bin", data)},
        data={"type": "binary", "name": "test_file.bin", "mime_type": "image/jpeg"},
        expected_status_code=204
    )

    resp = await assert_get(client, f"/logs/{log_id}/attachments/0")
    assert resp.headers["Content-Disposition"] == "attachment; filename=test_file.bin"
    assert resp.headers["Content-Type"] == "image/jpeg"
    assert resp.content == data


async def test_get_log_attachment_not_found_log_id(client: AsyncClient, db: Database):
    await assert_get(client, f"/logs/{UNKNOWN_LOG_ID}/attachments/0", expected_status_code=404)


async def test_get_log_attachment_not_found_attachment_idx(client: AsyncClient, db: Database):
    log = make_log_data()
    log_id = await prepare_log(client, log)

    await assert_get(client, f"/logs/{log_id}/attachments/0", expected_status_code=404)


async def test_get_logs(client: AsyncClient, db: Database):
    log1 = make_log_data()
    log2 = make_log_data()
    log1_id = await prepare_log(client, log1)
    log2_id = await prepare_log(client, log2)

    resp = await assert_get(client, "/logs")
    assert resp.json() == {
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


async def test_get_logs_limit(client: AsyncClient, db: Database):
    log1 = make_log_data()
    log2 = make_log_data()
    await prepare_log(client, log1)
    log2_id = await prepare_log(client, log2)

    resp = await assert_get(client, "/logs?limit=1")
    assert resp.json() == {
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


async def test_get_logs_limit_and_cursor(client: AsyncClient, db: Database):
    logs = []
    log_ids = []
    for _ in range(10):
        log = make_log_data()
        logs.append(log)
        log_id = await prepare_log(client, log)
        log_ids.append(log_id)

    # first step, get 5 logs and check the next_cursor
    resp = await assert_get(client, "/logs?limit=5")
    next_cursor = resp.json()["pagination"]["next_cursor"]
    assert next_cursor is not None
    assert resp.json()["data"] == [
        make_expected_log_data_for_api({**log, "id": log_id})
        for log, log_id in zip(reversed(logs[-5:]), reversed(log_ids[-5:]))
    ]

    # second step, get the next 5 logs using the next_cursor from the previous response and check next_cursor is None
    resp = await assert_get(client, f"/logs?limit=5&cursor={next_cursor}")
    assert resp.json()["pagination"]["next_cursor"] is None
    assert resp.json()["data"] == [
        make_expected_log_data_for_api({**log, "id": log_id})
        for log, log_id in zip(reversed(logs[:5]), reversed(log_ids[:5]))
    ]


async def _test_get_logs_filter(client: AsyncClient, func, params):
    log1 = make_log_data()
    await prepare_log(client, log1)
    log2 = make_log_data()
    func(log2)
    log2_id = await prepare_log(client, log2)

    resp = await assert_get(client, "/logs", params=params)
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


async def test_get_logs_filter_event_name(client: AsyncClient, db: Database):
    def func(log):
        log["event"]["name"] = "find_me"

    await _test_get_logs_filter(client, func, {"event_name": "find_me"})


async def test_get_logs_filter_event_category(client: AsyncClient, db: Database):
    def func(log):
        log["event"]["category"] = "find_me"

    await _test_get_logs_filter(client, func, {"event_category": "find_me"})


async def test_get_logs_filter_actor_type(client: AsyncClient, db: Database):
    def func(log):
        log["actor"] = {
            "type": "find_me",
            "id": "user:123",
            "name": "User 123"
        }

    await _test_get_logs_filter(client, func, {"actor_type": "find_me"})


async def test_get_logs_filter_actor_name(client: AsyncClient, db: Database):
    def func(log):
        log["actor"] = {
            "type": "user",
            "id": "user:123",
            "name": "find_me"
        }

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(client, func, {"actor_name": "FIND"})


async def test_get_logs_filter_resource_type(client: AsyncClient, db: Database):
    def func(log):
        log["resource"] = {
            "type": "find_me",
            "id": "core",
            "name": "Core Module"
        }

    await _test_get_logs_filter(client, func, {"resource_type": "find_me"})


async def test_get_logs_filter_resource_name(client: AsyncClient, db: Database):
    def func(log):
        log["resource"] = {
            "type": "module",
            "id": "core",
            "name": "find_me"
        }

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(client, func, {"resource_name": "FIND"})


async def test_get_logs_filter_tag_category(client: AsyncClient, db: Database):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "rich_tag:1", "category": "find_me", "name": "Rich tag"}
        ]

    await _test_get_logs_filter(client, func, {"tag_category": "find_me"})


async def test_get_logs_filter_tag_name(client: AsyncClient, db: Database):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "rich_tag:1", "category": "rich_tag", "name": "find_me"}
        ]

    # filter on tag_name is substring and case-insensitive
    await _test_get_logs_filter(client, func, {"tag_name": "FIND"})


async def test_get_logs_filter_tag_id(client: AsyncClient, db: Database):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "find_me", "category": "rich_tag", "name": "Rich tag"}
        ]

    await _test_get_logs_filter(client, func, {"tag_id": "find_me"})


async def test_get_logs_filter_node_id_exact_node(client: AsyncClient, db: Database):
    def func(log):
        log["node_path"] = [
            {"id": "find_me:1", "name": "Customer 1"},
            {"id": "find_me:2", "name": "Customer 2"}
        ]

    await _test_get_logs_filter(client, func, {"node_id": "find_me:2"})


async def test_get_logs_filter_node_id_ascendant_node(client: AsyncClient, db: Database):
    def func(log):
        log["node_path"] = [
            {"id": "find_me:1", "name": "Customer 1"},
            {"id": "find_me:2", "name": "Customer 2"}
        ]

    await _test_get_logs_filter(client, func, {"node_id": "find_me:1"})


async def test_get_logs_filter_multiple_criteria(client: AsyncClient, db: Database):
    log1 = make_log_data()
    log1["event"]["name"] = "find_me:event_name"
    await prepare_log(client, log1)

    log2 = make_log_data()
    log2["event"]["category"] = "find_me:event_category"
    await prepare_log(client, log2)

    log3 = make_log_data()
    log3["event"] = {"name": "find_me:event_name", "category": "find_me:event_category"}
    log3_id = await prepare_log(client, log3)

    resp = await assert_get(
        client,
        "/logs", params={"event_name": "find_me:event_name", "event_category": "find_me:event_category"}
    )
    assert resp.json() == {
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


async def test_get_logs_filter_no_result(client: AsyncClient, db: Database):
    log = make_log_data()
    await prepare_log(client, log)

    resp = await assert_get(client, "/logs", params={"event_name": "not to be found"})
    assert resp.json() == {
        "data": [],
        "pagination": {
            "next_cursor": None
        }
    }


async def _test_pagination_common_scenarii(client: AsyncClient, path: str, data: list):
    # first test, without pagination parameters
    resp = await assert_get(client, path)
    assert resp.json() == {
        "data": data,
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": len(data),
            "total_pages": 1
        }
    }

    # second test, with pagination parameters
    resp = await assert_get(client, path, params={"page": 2, "page_size": 2})
    assert resp.json() == {
        "data": data[2:4],
        "pagination": {
            "page": 2,
            "page_size": 2,
            "total": len(data),
            "total_pages": 3
        }
    }


async def test_get_log_event_categories(client: AsyncClient, db: Database):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_event(db, Log.Event(category=f"category_{i}", name=f"name_{i}"))
        await consolidate_log_event(db, Log.Event(category=f"category_{i}", name=f"name_{i + 10}"))

    await _test_pagination_common_scenarii(client, "/logs/event-categories", [f"category_{i}" for i in range(5)])


async def test_get_log_event_names(client: AsyncClient, db: Database):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_event(db, Log.Event(category=f"category_{i}", name=f"name_{i}"))
        await consolidate_log_event(db, Log.Event(category=f"category_{i + 10}", name=f"name_{i}"))

    await _test_pagination_common_scenarii(client, "/logs/events", [f"name_{i}" for i in range(5)])

    # test category parameter
    resp = await assert_get(client, "/logs/events?category=category_2")
    assert resp.json() == {
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


async def test_get_log_actor_types(client: AsyncClient, db: Database):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_actor(db, Log.Actor(type=f"type_{i}", id=f"id_{i}", name=f"name_{i}"))

    await _test_pagination_common_scenarii(client, "/logs/actor-types", [f"type_{i}" for i in range(5)])


async def test_get_log_resource_types(client: AsyncClient, db: Database):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_resource(db, Log.Resource(type=f"type_{i}", id=f"id_{i}", name=f"name_{i}"))

    await _test_pagination_common_scenarii(client, "/logs/resource-types", [f"type_{i}" for i in range(5)])


async def test_get_log_tag_categories(client: AsyncClient, db: Database):
    for i in reversed(range(5)):
        await consolidate_log_tags(db, [Log.Tag(id=f"tag_{i}", category=f"category_{i}", name=f"name_{i}")])
    await consolidate_log_tags(db, [Log.Tag(id="simple_tag")])  # no category, it must not be returned

    await _test_pagination_common_scenarii(client, "/logs/tag-categories", [f"category_{i}" for i in range(5)])


async def test_get_log_nodes_without_filters(client: AsyncClient, db: Database):
    for i in range(4):
        await consolidate_log_node_path(
            db, [Log.Node(id=f"customer", name=f"Customer"), Log.Node(id=f"entity:{i}", name=f"Entity {i}")]
        )

    await _test_pagination_common_scenarii(
        client, "/logs/nodes",
        [{"id": "customer", "name": "Customer", "parent_node_id": None}] +
        [{"id": f"entity:{i}", "name": f"Entity {i}", "parent_node_id": "customer"} for i in range(4)]
    )


async def test_get_log_nodes_with_filters(client: AsyncClient, db: Database):
    for i in range(5):
        for j in "a", "b", "c", "d", "e":
            await consolidate_log_node_path(
                db, [
                    Log.Node(id=f"customer:{i}", name=f"Customer {i}"),
                    Log.Node(id=f"entity:{i}-{j}", name=f"Entity {j}")
                ]
            )

    # test top-level nodes
    await _test_pagination_common_scenarii(
        client, "/logs/nodes?root=true",
        [{"id": f"customer:{i}", "name": f"Customer {i}", "parent_node_id": None} for i in range(5)]
    )

    # test non-top-level nodes
    await _test_pagination_common_scenarii(
        client, "/logs/nodes?parent_node_id=customer:2",
        [{"id": f"entity:2-{j}", "name": f"Entity {j}", "parent_node_id": "customer:2"}
         for j in ("a", "b", "c", "d", "e")]
    )
