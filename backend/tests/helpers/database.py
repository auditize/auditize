import random

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from auditize.common.db import DatabaseManager, get_dbm
from auditize.logs.db import get_logs_db_name
from auditize.main import app


def setup_test_dbm():
    mongo_client = AsyncIOMotorClient()
    test_dbm = DatabaseManager.spawn(
        client=mongo_client, name_prefix="test_%04d" % int(random.random() * 10000)
    )
    app.dependency_overrides[get_dbm] = lambda: test_dbm
    return test_dbm


async def teardown_test_dbm(test_dbm):
    app.dependency_overrides[get_dbm] = get_dbm

    # Drop logs databases and core database
    async for repo in test_dbm.core_db.repos.find({}):
        await test_dbm.client.drop_database(get_logs_db_name(test_dbm, repo["_id"]))
    await test_dbm.core_db.client.drop_database(test_dbm.core_db.name)

    test_dbm.client.close()


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected
