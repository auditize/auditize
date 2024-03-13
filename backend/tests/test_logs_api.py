import pytest
from httpx import AsyncClient
from icecream import ic

pytestmark = pytest.mark.anyio


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
        "occurred_at": "2021-01-01T12:00:00.000Z",
        "node_path": [
            {
                "id": "1",
                "name": "Customer 1"
            }
        ],
        **extra
    }


async def assert_post(client: AsyncClient, path, json=None, files=None, data=None, expected_status_code=200):
    ic(json, files, data)
    resp = await client.post(path, json=json, files=files, data=data)
    ic(resp.json())
    assert resp.status_code == expected_status_code
    return resp


async def assert_create_log(client: AsyncClient, log: dict, expected_status_code=201):
    resp = await assert_post(client, "/logs", json=log, expected_status_code=expected_status_code)
    if expected_status_code == 201:
        assert "id" in resp.json()
    return resp


async def test_create_log_minimal_fields(client: AsyncClient):
    log = make_log_data()
    await assert_create_log(client, log)


async def test_create_log_all_fields(client: AsyncClient):
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
                "type": "rich_tag",
                "name": "Rich tag"
            }
        ],
    })

    await assert_create_log(client, log)


async def test_create_log_missing_event_name(client: AsyncClient):
    log = make_log_data()
    del log["event"]["name"]
    await assert_create_log(client, log, expected_status_code=422)


async def test_create_log_invalid_rich_tag(client: AsyncClient):
    invalid_tags = (
        {"id": "some_tag", "type": "rich_tag"},
        {"id": "some_other_tag", "name": "Rich tag"}
    )

    for invalid_tag in invalid_tags:
        await assert_create_log(client, make_log_data({"tags": [invalid_tag]}), expected_status_code=422)


async def test_add_attachment(client: AsyncClient):
    resp = await assert_create_log(client, make_log_data())
    log_id = resp.json()["id"]

    await assert_post(
        client,
        f"/logs/{log_id}/attachments",
        files={"file": ("test.txt", b"test data")},
        data={"type": "text", "name": "test_file.txt", "mime_type": "text/plain"},
        expected_status_code=200
    )
