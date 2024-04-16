import pytest


pytest.register_assert_rewrite("helpers")
from helpers import create_http_client, setup_test_dbm, teardown_test_dbm, RepoTest


@pytest.fixture(scope="session")
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return 'asyncio'


@pytest.fixture(scope="session")
async def client():
    async with create_http_client() as client:
        yield client


@pytest.fixture(scope="function")
async def dbm():
    test_dbm = setup_test_dbm()
    await test_dbm.setup()
    yield test_dbm
    await teardown_test_dbm(test_dbm)


@pytest.fixture(scope="function")
async def repo(dbm):
    return await RepoTest.create(dbm)
