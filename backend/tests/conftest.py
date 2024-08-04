import os
from typing import Awaitable, Callable, Optional, Protocol

import pytest
from icecream import ic

ic.configureOutput(includeContext=True)

# We must initialize the environment before the auditize modules (and more specifically
# auditize.config) get loaded.
# Otherwise, the FastAPI app will be loaded with a configuration based on
# the system, non-controlled, environment.
# Unfortunately, we can't use the pytest-env plugin because it does not support clearing
# environment variables.

for key in os.environ:
    if key.startswith("AUDITIZE_") or key.startswith("_AUDITIZE_"):
        del os.environ[key]

os.environ.update(
    # set the environment variables (at least the required ones)
    {
        "AUDITIZE_JWT_SIGNING_KEY": "917c5d359493bf90140e4f725b351d2282a6c23bb78d096cb7913d7090375a73",
        "AUDITIZE_ATTACHMENT_MAX_SIZE": "1024",
        "AUDITIZE_CSV_MAX_ROWS": "10",
        "_AUDITIZE_TEST_MODE": "true",
    }
)

from auditize.database import DatabaseManager
from auditize.logs.db import LogDatabase

pytest.register_assert_rewrite("helpers")
from helpers.apikeys import PreparedApikey
from helpers.database import (
    TestLogDatabasePool,
    cleanup_db,
    setup_test_dbm,
    teardown_test_dbm,
)
from helpers.http import HttpTestHelper
from helpers.logi18nprofiles import PreparedLogI18nProfile
from helpers.repos import PreparedRepo
from helpers.users import PreparedUser


@pytest.fixture(scope="session")
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return "asyncio"


@pytest.fixture(scope="function")
async def apikey_client(dbm: DatabaseManager):
    apikey = await PreparedApikey.inject_into_db(dbm)
    async with apikey.client() as client:
        yield client


# the default client fixture is based on apikey
@pytest.fixture(scope="function")
async def client(apikey_client):
    yield apikey_client


@pytest.fixture(scope="function")
async def user_client(dbm: DatabaseManager):
    user = await PreparedUser.inject_into_db(dbm)
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def anon_client():
    async with HttpTestHelper.spawn() as client:
        yield client


@pytest.fixture(scope="session")
async def _dbm():
    test_dbm = setup_test_dbm()
    await test_dbm.setup()
    yield test_dbm
    await teardown_test_dbm(test_dbm)


@pytest.fixture(scope="session")
async def _log_db(_dbm: DatabaseManager):
    log_db = LogDatabase(_dbm.name_prefix + "_logs", _dbm.client)
    await log_db.setup()
    return log_db


@pytest.fixture(scope="session")
async def _log_db_pool(_dbm: DatabaseManager):
    return TestLogDatabasePool(_dbm)


@pytest.fixture(scope="function")
async def dbm(_dbm):
    yield _dbm
    await cleanup_db(_dbm.core_db.db)


RepoBuilder = Callable[[dict], Awaitable[PreparedRepo]]


@pytest.fixture(scope="function")
async def repo_builder(dbm, _log_db_pool) -> RepoBuilder:
    async def func(extra):
        return await PreparedRepo.create(
            dbm, PreparedRepo.prepare_data(extra), log_db=await _log_db_pool.get_db()
        )

    yield func
    await _log_db_pool.release()


@pytest.fixture(scope="function")
async def repo(repo_builder):
    return await repo_builder({})


@pytest.fixture(scope="function")
async def log_i18n_profile(dbm):
    return await PreparedLogI18nProfile.create(dbm)


@pytest.fixture(scope="function")
async def user(superadmin_client, dbm):
    return await PreparedUser.create(superadmin_client, dbm)


@pytest.fixture(scope="function")
async def apikey(dbm):
    return await PreparedApikey.inject_into_db(dbm)


ApikeyBuilder = Callable[[dict], Awaitable[PreparedApikey]]


@pytest.fixture(scope="function")
def apikey_builder(dbm) -> ApikeyBuilder:
    async def func(permissions):
        return await PreparedApikey.inject_into_db_with_permissions(dbm, permissions)

    return func


class UserBuilder(Protocol):
    async def __call__(
        self, permissions: dict, lang: Optional[str] = None
    ) -> PreparedUser: ...


@pytest.fixture(scope="function")
def user_builder(dbm) -> UserBuilder:
    async def func(permissions, lang=None):
        return await PreparedUser.inject_into_db(
            dbm,
            user=PreparedUser.prepare_model(
                password="dummypassword", permissions=permissions, lang=lang
            ),
            password="dummypassword",
        )

    return func


@pytest.fixture(scope="function")
async def no_permission_client(apikey_builder):
    apikey = await apikey_builder({})  # {} == no permissions
    async with apikey.client() as client:
        yield client


@pytest.fixture(scope="function")
async def superadmin_client(apikey_builder):
    apikey = await apikey_builder({"is_superadmin": True})
    async with apikey.client() as client:
        yield client


@pytest.fixture(scope="function")
async def repo_read_client(apikey_builder):
    apikey = await apikey_builder({"management": {"repos": {"read": True}}})
    async with apikey.client() as client:
        yield client


@pytest.fixture(scope="function")
async def repo_write_client(apikey_builder):
    apikey = await apikey_builder({"management": {"repos": {"write": True}}})
    async with apikey.client() as client:
        yield client


@pytest.fixture(scope="function")
async def apikey_read_client(user_builder):
    user = await user_builder({"management": {"apikeys": {"read": True}}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def apikey_write_client(user_builder):
    user = await user_builder({"management": {"apikeys": {"write": True}}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def apikey_rw_client(user_builder):
    user = await user_builder(
        {"management": {"apikeys": {"read": True, "write": True}}}
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def user_read_client(apikey_builder):
    apikey = await apikey_builder({"management": {"users": {"read": True}}})
    async with apikey.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def user_write_client(apikey_builder):
    apikey = await apikey_builder({"management": {"users": {"write": True}}})
    async with apikey.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def user_rw_client(apikey_builder):
    apikey = await apikey_builder(
        {"management": {"users": {"read": True, "write": True}}}
    )
    async with apikey.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def log_read_client(apikey_builder):
    apikey = await apikey_builder({"logs": {"read": True}})
    async with apikey.client() as client:
        yield client


@pytest.fixture(scope="function")
async def log_read_user(user_builder):
    return await user_builder({"logs": {"read": True}})


@pytest.fixture(scope="function")
async def log_read_user_client(log_read_user):
    async with log_read_user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def log_write_client(apikey_builder):
    apikey = await apikey_builder({"logs": {"write": True}})
    async with apikey.client() as client:
        yield client


@pytest.fixture(scope="function")
async def log_rw_client(apikey_builder):
    apikey = await apikey_builder({"logs": {"read": True, "write": True}})
    async with apikey.client() as client:
        yield client
