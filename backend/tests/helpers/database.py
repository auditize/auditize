import random

from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.common.mongo import DatabaseManager, get_dbm
from auditize.main import app


def setup_test_dbm():
    test_dbm = DatabaseManager.spawn(base_name="test_%04d" % int(random.random() * 10000))
    app.dependency_overrides[get_dbm] = lambda: test_dbm
    return test_dbm


async def teardown_test_dbm(test_dbm):
    app.dependency_overrides[get_dbm] = get_dbm

    # Drop repos databases and core database
    async for repo in test_dbm.core_db.repos.find({}):
        await test_dbm.client.drop_database(test_dbm.get_repo_db_name(repo["_id"]))
    await test_dbm.core_db.client.drop_database(test_dbm.core_db.name)


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected
