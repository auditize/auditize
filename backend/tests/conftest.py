import os

import pytest

pytest.register_assert_rewrite("helpers")
from helpers.database import setup_test_dbm, teardown_test_dbm
from helpers.http import create_http_client
from helpers.repos import PreparedRepo
from helpers.users import PreparedUser
from helpers.integrations import PreparedIntegration


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    # clean slate
    for key in os.environ:
        if key.startswith("AUDITIZE_"):
            del os.environ[key]

    # set the environment variables (at least the required ones)
    os.environ.update({
        "AUDITIZE_USER_SESSION_TOKEN_SIGNING_KEY": "917c5d359493bf90140e4f725b351d2282a6c23bb78d096cb7913d7090375a73"
    })


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
async def user(client, dbm):
    return await PreparedUser.create(client, dbm)


@pytest.fixture(scope="function")
async def integration(client, dbm):
    return await PreparedIntegration.create(client, dbm)
