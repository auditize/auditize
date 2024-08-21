import os
import random

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from auditize.database import DatabaseManager, init_dbm
from auditize.log.db import LogDatabase


def setup_test_dbm():
    name_prefix = "test_%04d" % int(random.random() * 10000)
    try:
        name_prefix += "_" + os.environ["PYTEST_XDIST_WORKER"]
    except KeyError:
        pass
    return init_dbm(name_prefix, force_init=True)


async def teardown_test_dbm(test_dbm):
    for db_name in await test_dbm.client.list_database_names():
        if db_name.startswith(test_dbm.name_prefix):
            await test_dbm.client.drop_database(db_name)

    test_dbm.client.close()


async def assert_collection(
    collection: AsyncIOMotorCollection, expected, *, filter=None
):
    results = await collection.find(filter or {}).to_list(None)
    assert results == expected


async def cleanup_db(db: AsyncIOMotorDatabase):
    for collection_name in await db.list_collection_names():
        await db[collection_name].delete_many({})


class TestLogDatabasePool:
    def __init__(self, dbm: DatabaseManager):
        self.dbm = dbm
        self._cache = {}

    async def get_db(self) -> LogDatabase:
        for db, is_used in self._cache.items():
            if not is_used:
                self._cache[db] = True
                return db
        else:
            db = LogDatabase(
                f"{self.dbm.name_prefix}_logs_{len(self._cache)}", self.dbm.client
            )
            await db.setup()
            self._cache[db] = True
            return db

    async def release(self):
        for db, is_used in self._cache.items():
            if is_used:
                await cleanup_db(db.db)
                self._cache[db] = False
