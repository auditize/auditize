import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.anyio


async def test_create_log(client: AsyncClient):
    resp = await client.post(
        "/logs",
        json={
            "event": {
                "name": "user_login",
                "category": "authentication",
            },
            "occurred_at": "2021-01-01T12:00:00",
        },
    )
    assert resp.status_code == 200
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
