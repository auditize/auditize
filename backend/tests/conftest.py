from typing import Awaitable, Callable, Optional, Protocol

import pytest
from icecream import ic

from auditize.config import init_config
from auditize.database import CoreDatabase, Database, migrate_core_db
from auditize.log.db import LogDatabase
from auditize.log.service import _CONSOLIDATED_DATA_CACHE

ic.configureOutput(includeContext=True)

pytest.register_assert_rewrite("helpers")
from helpers.apikey import PreparedApikey
from helpers.database import (
    TestLogDatabasePool,
    cleanup_db,
    setup_test_core_db,
    teardown_test_core_db,
)
from helpers.http import HttpTestHelper
from helpers.log_i18n_profile import PreparedLogI18nProfile
from helpers.repo import PreparedRepo
from helpers.user import PreparedUser


@pytest.fixture(scope="session")
def anyio_backend():
    # Limit the tests to only run on asyncio:
    return "asyncio"


@pytest.fixture(scope="session", autouse=True)
def _config(anyio_backend):
    init_config(
        {
            "AUDITIZE_PUBLIC_URL": "http://localhost:8000",
            "AUDITIZE_JWT_SIGNING_KEY": "917c5d359493bf90140e4f725b351d2282a6c23bb78d096cb7913d7090375a73",
            "AUDITIZE_ATTACHMENT_MAX_SIZE": "1024",
            "AUDITIZE_CSV_MAX_ROWS": "10",
            "_AUDITIZE_TEST_MODE": "true",
        }
    )


@pytest.fixture(scope="session")
async def _core_db():
    test_db = setup_test_core_db()
    await migrate_core_db()
    yield test_db
    await teardown_test_core_db(test_db)


@pytest.fixture(scope="function")
async def apikey_client():
    apikey = await PreparedApikey.inject_into_db()
    async with apikey.client() as client:
        yield client


# the default client fixture is based on apikey
@pytest.fixture(scope="function")
async def client(apikey_client):
    yield apikey_client


@pytest.fixture(scope="function")
async def user_client():
    user = await PreparedUser.inject_into_db()
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        yield client


@pytest.fixture(scope="function")
async def anon_client():
    async with HttpTestHelper.spawn() as client:
        yield client


@pytest.fixture(scope="session")
async def _log_db(_core_db: CoreDatabase):
    log_db = LogDatabase(_core_db.name + "_logs", _core_db.client)
    await log_db.setup()
    return log_db


@pytest.fixture(scope="session")
async def _log_db_pool(_core_db: CoreDatabase):
    return TestLogDatabasePool(_core_db)


@pytest.fixture(scope="function", autouse=True)
async def core_db(_core_db, anyio_backend):
    yield _core_db
    await cleanup_db(_core_db)
    await _CONSOLIDATED_DATA_CACHE.clear()


@pytest.fixture(scope="function")
async def tmp_db(_core_db: CoreDatabase):
    db = Database(_core_db.name + "_tmp", _core_db.client)
    yield db
    await db.client.drop_database(db.name)


RepoBuilder = Callable[[dict], Awaitable[PreparedRepo]]


@pytest.fixture(scope="function")
async def repo_builder(core_db, _log_db_pool) -> RepoBuilder:
    async def func(extra):
        return await PreparedRepo.create(
            PreparedRepo.prepare_data(extra), log_db=await _log_db_pool.get_db()
        )

    yield func
    await _log_db_pool.release()


@pytest.fixture(scope="function")
async def repo(repo_builder):
    return await repo_builder({})


@pytest.fixture(scope="function")
async def log_i18n_profile():
    return await PreparedLogI18nProfile.create()


@pytest.fixture(scope="function")
async def user(superadmin_client):
    return await PreparedUser.create(superadmin_client)


@pytest.fixture(scope="function")
async def apikey():
    return await PreparedApikey.inject_into_db()


ApikeyBuilder = Callable[[dict], Awaitable[PreparedApikey]]


@pytest.fixture(scope="function")
def apikey_builder(core_db) -> ApikeyBuilder:
    async def func(permissions):
        return await PreparedApikey.inject_into_db_with_permissions(permissions)

    return func


class UserBuilder(Protocol):
    async def __call__(
        self, permissions: dict, lang: Optional[str] = None
    ) -> PreparedUser: ...


@pytest.fixture(scope="function")
def user_builder(core_db) -> UserBuilder:
    async def func(permissions, lang=None):
        return await PreparedUser.inject_into_db(
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
