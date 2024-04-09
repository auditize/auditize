import pytest

pytest.register_assert_rewrite("helpers")

from helpers import create_http_client, setup_test_db, teardown_test_db


@pytest.fixture(scope="session")
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return 'asyncio'


@pytest.fixture(scope="session")
async def client():
    async with create_http_client() as client:
        yield client


@pytest.fixture(scope="function")
async def db():
    test_db = setup_test_db()
    await test_db.setup()
    yield test_db
    await teardown_test_db(test_db)
