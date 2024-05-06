import os
from typing import Awaitable, Callable

import pytest

from auditize.common.db import DatabaseManager

pytest.register_assert_rewrite("helpers")
from helpers.database import setup_test_dbm, teardown_test_dbm
from helpers.http import HttpTestHelper, create_http_client
from helpers.integrations import PreparedIntegration
from helpers.repos import PreparedRepo
from helpers.users import PreparedUser


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    # clean slate
    for key in os.environ:
        if key.startswith("AUDITIZE_"):
            del os.environ[key]

    # set the environment variables (at least the required ones)
    os.environ.update(
        {
            "AUDITIZE_JWT_SIGNING_KEY": "917c5d359493bf90140e4f725b351d2282a6c23bb78d096cb7913d7090375a73"
        }
    )


@pytest.fixture(scope="session")
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return "asyncio"


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
async def user(superadmin_client, dbm):
    return await PreparedUser.create(superadmin_client, dbm)


@pytest.fixture(scope="function")
async def integration(dbm):
    return await PreparedIntegration.inject_into_db(dbm)


IntegrationBuilder = Callable[[dict], Awaitable[PreparedIntegration]]


@pytest.fixture(scope="function")
def integration_builder(dbm) -> IntegrationBuilder:
    async def func(permissions):
        return await PreparedIntegration.inject_into_db_with_permissions(
            dbm, permissions
        )

    return func


UserBuilder = Callable[[dict], Awaitable[PreparedUser]]


@pytest.fixture(scope="function")
def user_builder(dbm) -> UserBuilder:
    async def func(permissions):
        return await PreparedUser.inject_into_db(
            dbm,
            user=PreparedUser.prepare_model(password="dummy", permissions=permissions),
            password="dummy",
        )

    return func


@pytest.fixture(scope="function")
async def no_permission_client(integration_builder):
    integration = await integration_builder({})  # {} == no permissions
    async with integration.client() as client:
        yield client


@pytest.fixture(scope="function")
async def superadmin_client(integration_builder):
    integration = await integration_builder({"is_superadmin": True})
    async with integration.client() as client:
        yield client


@pytest.fixture(scope="function")
async def repo_read_client(integration_builder):
    integration = await integration_builder({"entities": {"repos": {"read": True}}})
    async with integration.client() as client:
        yield client


@pytest.fixture(scope="function")
async def repo_write_client(integration_builder):
    integration = await integration_builder({"entities": {"repos": {"write": True}}})
    async with integration.client() as client:
        yield client


@pytest.fixture(scope="function")
async def integration_read_client(user_builder):
    user = await user_builder({"entities": {"integrations": {"read": True}}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def integration_write_client(user_builder):
    user = await user_builder({"entities": {"integrations": {"write": True}}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def integration_rw_client(user_builder):
    user = await user_builder(
        {"entities": {"integrations": {"read": True, "write": True}}}
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def user_read_client(integration_builder):
    integration = await integration_builder({"entities": {"users": {"read": True}}})
    async with integration.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def user_write_client(integration_builder):
    integration = await integration_builder({"entities": {"users": {"write": True}}})
    async with integration.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def user_rw_client(integration_builder):
    integration = await integration_builder(
        {"entities": {"users": {"read": True, "write": True}}}
    )
    async with integration.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def log_read_client(integration_builder):
    integration = await integration_builder({"logs": {"read": True}})
    async with integration.client() as client:
        yield client


@pytest.fixture(scope="function")
async def log_write_client(integration_builder):
    integration = await integration_builder({"logs": {"write": True}})
    async with integration.client() as client:
        yield client


@pytest.fixture(scope="function")
async def log_rw_client(integration_builder):
    integration = await integration_builder({"logs": {"read": True, "write": True}})
    async with integration.client() as client:
        yield client
