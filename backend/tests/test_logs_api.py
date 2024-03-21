import time
import datetime
from bson import ObjectId
import base64

import pytest
import callee
from httpx import AsyncClient
from icecream import ic

from auditize.common.mongo import Database


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
    return expected


async def assert_post(client: AsyncClient, path, json=None, files=None, data=None, expected_status_code=200):
    ic(json, files, data)
    resp = await client.post(path, json=json, files=files, data=data)
    ic(resp.text)
    assert resp.status_code == expected_status_code
    return resp


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

    resp = await client.get(f"/logs/{log_id}")
    assert resp.status_code == 200
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

    resp = await client.get(f"/logs/{log_id}")
    assert resp.status_code == 200
    assert resp.json() == make_expected_log_data_for_api({
        **log,
        "id": log_id
    })


async def test_get_log_not_found(client: AsyncClient, db: Database):
    resp = await client.get(f"/logs/{UNKNOWN_LOG_ID}")
    assert resp.status_code == 404


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

    resp = await client.get(f"/logs/{log_id}/attachments/0")
    assert resp.status_code == 200
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

    resp = await client.get(f"/logs/{log_id}/attachments/0")
    assert resp.status_code == 200
    assert resp.headers["Content-Disposition"] == "attachment; filename=test_file.bin"
    assert resp.headers["Content-Type"] == "image/jpeg"
    assert resp.content == data


async def test_get_log_attachment_not_found_log_id(client: AsyncClient, db: Database):
    resp = await client.get(f"/logs/{UNKNOWN_LOG_ID}/attachments/0")
    assert resp.status_code == 404


async def test_get_log_attachment_not_found_attachment_idx(client: AsyncClient, db: Database):
    log = make_log_data()
    log_id = await prepare_log(client, log)

    resp = await client.get(f"/logs/{log_id}/attachments/0")
    assert resp.status_code == 404


async def test_get_logs(client: AsyncClient, db: Database):
    log1 = make_log_data()
    log2 = make_log_data()
    log1_id = await prepare_log(client, log1)
    log2_id = await prepare_log(client, log2)

    resp = await client.get("/logs")
    assert resp.status_code == 200
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

    resp = await client.get("/logs?limit=1")
    assert resp.status_code == 200
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
    resp = await client.get("/logs?limit=5")
    assert resp.status_code == 200
    next_cursor = resp.json()["pagination"]["next_cursor"]
    assert next_cursor is not None
    assert resp.json()["data"] == [
        make_expected_log_data_for_api({**log, "id": log_id})
        for log, log_id in zip(reversed(logs[-5:]), reversed(log_ids[-5:]))
    ]

    # second step, get the next 5 logs using the next_cursor from the previous response and check next_cursor is None
    resp = await client.get(f"/logs?limit=5&cursor={next_cursor}")
    assert resp.status_code == 200
    assert resp.json()["pagination"]["next_cursor"] is None
    assert resp.json()["data"] == [
        make_expected_log_data_for_api({**log, "id": log_id})
        for log, log_id in zip(reversed(logs[:5]), reversed(log_ids[:5]))
    ]
