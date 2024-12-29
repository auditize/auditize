import os
import random

from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.database import Database, DatabaseManager, init_dbm
from auditize.log.service import create_indices


def setup_test_dbm() -> DatabaseManager:
    db_name = "test_%04d" % int(random.random() * 10000)
    try:
        db_name += "_" + os.environ["PYTEST_XDIST_WORKER"]
    except KeyError:
        pass
    return init_dbm(db_name, force_init=True)


async def teardown_test_dbm(dbm: DatabaseManager):
    for index_name in await dbm.elastic_client.indices.get_alias(
        index=dbm.core_db.name + "*"
    ):
        if index_name.startswith(dbm.core_db.name):
            await dbm.elastic_client.indices.delete(index=index_name)

    dbm.core_db.client.close()


async def cleanup_db(db: Database):
    for collection_name in await db.db.list_collection_names():
        await db.db[collection_name].delete_many({})


class TestLogDatabasePool:
    def __init__(self, dbm: DatabaseManager):
        self.dbm = dbm
        self._cache = {}

    async def get_db_name(self) -> str:
        for db_name, is_used in self._cache.items():
            if not is_used:
                self._cache[db_name] = True
                return db_name
        else:
            db_name = f"{self.dbm.core_db.name}_logs_{len(self._cache)}"
            await create_indices(self.dbm.elastic_client, db_name)
            self._cache[db_name] = True
            return db_name

    async def release(self):
        for db_name, is_used in self._cache.items():
            if is_used:
                es_client = self.dbm.elastic_client
                await es_client.delete_by_query(
                    index=db_name, body={"query": {"match_all": {}}}, refresh=True
                )
                await es_client.delete_by_query(
                    index=f"{db_name}_entities",
                    body={"query": {"match_all": {}}},
                    refresh=True,
                )
                self._cache[db_name] = False


async def assert_collection(
    collection: AsyncIOMotorCollection, expected, *, filter=None
):
    results = await collection.find(filter or {}).to_list(None)
    assert results == expected


async def assert_db_indexes(db: Database, expected):
    assert list(sorted(await db.db.list_collection_names())) == list(
        sorted(expected.keys())
    )
    for collection_name, expected_indexes in expected.items():
        actual_indexes = [
            index["name"] async for index in db.db[collection_name].list_indexes()
        ]
        assert list(sorted(actual_indexes)) == list(
            sorted(expected_indexes + ("_id_",))
        )
