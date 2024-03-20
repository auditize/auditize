import uuid

import pytest
from httpx import AsyncClient, ASGITransport

from auditize.main import app
from auditize.common.mongo import mongo_client, get_db, Database


@pytest.fixture(scope="session")
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return 'asyncio'


@pytest.fixture(scope="session")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost") as client:
        yield client


@pytest.fixture(scope="function")
async def db():
    new_db = Database("test_%s" % uuid.uuid4(), mongo_client)
    app.dependency_overrides[get_db] = lambda: new_db
    yield new_db
    app.dependency_overrides[get_db] = get_db
    await mongo_client.drop_database(new_db.name)
