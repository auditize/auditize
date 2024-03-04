import pytest

from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return 'asyncio'


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        yield client
