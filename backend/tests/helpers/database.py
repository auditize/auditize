import os
import random

from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.database import DatabaseManager, get_dbm, setup_mongo_client
from auditize.main import app


def setup_test_dbm():
    mongo_client = setup_mongo_client()
    name_prefix = "test_%04d" % int(random.random() * 10000)
    try:
        name_prefix += "_" + os.environ["PYTEST_XDIST_WORKER"]
    except KeyError:
        pass
    test_dbm = DatabaseManager.spawn(client=mongo_client, name_prefix=name_prefix)
    app.dependency_overrides[get_dbm] = lambda: test_dbm
    return test_dbm


async def teardown_test_dbm(test_dbm):
    app.dependency_overrides[get_dbm] = get_dbm

    # Drop logs databases and core database
    async for repo in test_dbm.core_db.repos.find({}):
        await test_dbm.client.drop_database(repo["log_db_name"])
    await test_dbm.core_db.client.drop_database(test_dbm.core_db.name)

    test_dbm.client.close()


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected
