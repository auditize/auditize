import pytest


pytest.register_assert_rewrite("helpers")
from helpers.database import setup_test_dbm, teardown_test_dbm
from helpers.http import create_http_client
from helpers.repos import PreparedRepo
from helpers.users import PreparedUser


@pytest.fixture(scope="session")
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return 'asyncio'


@pytest.fixture(scope="session")
async def client():
    async with create_http_client() as client:
        yield client


@pytest.fixture(scope="function", autouse=True)
async def dbm():
    test_dbm = setup_test_dbm()
    await test_dbm.setup()
    yield test_dbm
    await teardown_test_dbm(test_dbm)


@pytest.fixture(scope="function")
async def repo(dbm):
    return await PreparedRepo.create(dbm)


@pytest.fixture(scope="function")
async def user(client):
    return await PreparedUser.create(client)
