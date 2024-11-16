import os
import random

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase

from auditize.database import CoreDatabase, Database, init_core_db
from auditize.log.db import LogDatabase


def setup_test_core_db() -> CoreDatabase:
    db_name = "test_%04d" % int(random.random() * 10000)
    try:
        db_name += "_" + os.environ["PYTEST_XDIST_WORKER"]
    except KeyError:
        pass
    return init_core_db(db_name, force_init=True)


async def teardown_test_core_db(core_db: CoreDatabase):
    for db_name in await core_db.client.list_database_names():
        if db_name.startswith(core_db.name):
            await core_db.client.drop_database(db_name)

    core_db.client.close()


async def assert_collection(
    collection: AsyncIOMotorCollection, expected, *, filter=None
):
    results = await collection.find(filter or {}).to_list(None)
    assert results == expected


async def cleanup_db(db: Database):
    for collection_name in await db.db.list_collection_names():
        await db.db[collection_name].delete_many({})


class TestLogDatabasePool:
    def __init__(self, core_db: CoreDatabase):
        self.core_db = core_db
        self._cache = {}

    async def get_db(self) -> LogDatabase:
        for log_db, is_used in self._cache.items():
            if not is_used:
                self._cache[log_db] = True
                return log_db
        else:
            log_db = LogDatabase(
                f"{self.core_db.name}_logs_{len(self._cache)}", self.core_db.client
            )
            await log_db.setup()
            self._cache[log_db] = True
            return log_db

    async def release(self):
        for log_db, is_used in self._cache.items():
            if is_used:
                await cleanup_db(log_db)
                self._cache[log_db] = False
