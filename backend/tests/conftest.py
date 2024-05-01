from typing import Callable, Awaitable
import os

import pytest

from auditize.common.db import DatabaseManager

pytest.register_assert_rewrite("helpers")
from helpers.database import setup_test_dbm, teardown_test_dbm
from helpers.http import create_http_client, HttpTestHelper
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


@pytest.fixture(scope="function")
async def integration_client(dbm: DatabaseManager):
    integration = await PreparedIntegration.inject_into_db(dbm)
    async with integration.client() as client:
        yield client


# the default client fixture is based on integration
@pytest.fixture(scope="function")
async def client(integration_client):
    yield integration_client


@pytest.fixture(scope="function")
async def user_client(dbm: DatabaseManager):
    user = await PreparedUser.inject_into_db(dbm)
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def anon_client():
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
async def integration(user_client, dbm):
    # use user_client instead of integration_client to let an empty integrations collection
    # when testing integrations
    return await PreparedIntegration.create(user_client, dbm)


@pytest.fixture(scope="function")
def integration_builder(dbm):
    async def func(permissions):
        return await PreparedIntegration.inject_into_db_with_permissions(
            dbm, permissions
        )
    return func


IntegrationBuilder = Callable[[dict], Awaitable[PreparedIntegration]]


@pytest.fixture(scope="function")
def user_builder(dbm):
    async def func(permissions):
        return await PreparedUser.inject_into_db(
            dbm,
            user=PreparedUser.prepare_model(password="dummy", permissions=permissions),
            password="dummy"
        )
    return func


UserBuilder = Callable[[dict], Awaitable[PreparedUser]]
