import os
import random

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

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

    for db_name in await test_dbm.client.list_database_names():
        if db_name.startswith(test_dbm.name_prefix):
            await test_dbm.client.drop_database(db_name)

    test_dbm.client.close()


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected


async def cleanup_db(db: AsyncIOMotorDatabase):
    for collection_name in await db.list_collection_names():
        await db[collection_name].delete_many({})
