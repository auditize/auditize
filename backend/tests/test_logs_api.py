import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_create_log_minimal_fields(client: AsyncClient):
    resp = await client.post(
        "/logs",
        json={
            "event": {
                "name": "user_login",
                "category": "authentication",
            },
            "occurred_at": "2021-01-01T12:00:00.000Z",
        },
    )
    print(resp.json())
    assert resp.status_code == 201
    assert "id" in resp.json()


async def test_create_log_all_fields(client: AsyncClient):
    resp = await client.post(
        "/logs",
        json={
            "event": {
                "name": "user_login",
                "category": "authentication",
            },
            "occurred_at": "2021-01-01T12:00:00.000Z",
            "source": {
                "ip": "1.1.1.1",
                "user_agent": "Mozilla/5.0"
            },
            "actor": {
                "type": "user",
                "id": "user:123",
                "name": "User 123"
            },
            "resource": {
                "type": "module",
                "id": "core",
                "name": "Core Module"
            },
            "context": {
                "more_details": {
                    "some_key": "some_value"
                },
                "other_details": {
                    "other_key": "other_value"
                }
            }
        }
    )
    print(resp.json())
    assert resp.status_code == 201
    assert "id" in resp.json()


async def test_create_log_missing_event_name(client: AsyncClient):
    resp = await client.post(
        "/logs",
        json={
            "event": {
                "category": "authentication",
            },
            "occurred_at": "2021-01-01T12:00:00",
        },
    )
    assert resp.status_code == 422
