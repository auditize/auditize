import os
import random

import elasticsearch
from motor.motor_asyncio import AsyncIOMotorCollection
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.testing import future

from auditize.config import get_config
from auditize.database import Database, DatabaseManager, init_dbm
from auditize.database.dbm import SqlModel
from auditize.log.service import create_indices


def setup_test_dbm() -> DatabaseManager:
    db_name = "test_%04d" % int(random.random() * 10000)
    try:
        db_name += "_" + os.environ["PYTEST_XDIST_WORKER"]
    except KeyError:
        pass
    return init_dbm(db_name, force_init=True, debug=False)


async def teardown_test_dbm(dbm: DatabaseManager):
    for index_name in await dbm.elastic_client.indices.get_alias(
        index=dbm.core_db.name + "*"
    ):
        if index_name.startswith(dbm.core_db.name):
            await dbm.elastic_client.indices.delete(index=index_name)

    await dbm.core_db.client.drop_database(dbm.core_db.name)

    dbm.core_db.client.close()


async def cleanup_db(db: Database):
    for collection_name in await db.db.list_collection_names():
        await db.db[collection_name].delete_many({})


async def create_pg_db(dbm: DatabaseManager):
    config = get_config()
    pg_url = "postgresql+asyncpg://%s:%s@%s:5432/postgres" % (
        config.postgres_user,
        config.postgres_user_password,
        config.postgres_host,
    )
    engine = create_async_engine(pg_url)
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text(f"CREATE DATABASE {dbm.core_db.name}"))

    async with dbm.db_engine.begin() as conn:
        await conn.run_sync(SqlModel.metadata.create_all)


async def truncate_pg_db(dbm: DatabaseManager):
    async with dbm.db_engine.begin() as conn:
        table_names = [table.name for table in SqlModel.metadata.sorted_tables]
        table_names_as_str = ", ".join(f'"{name}"' for name in table_names)
        await conn.execute(
            text(f"TRUNCATE TABLE {table_names_as_str} RESTART IDENTITY CASCADE")
        )


async def drop_pg_db(dbm: DatabaseManager):
    config = get_config()
    pg_url = "postgresql+asyncpg://%s:%s@%s:5432/postgres" % (
        config.postgres_user,
        config.postgres_user_password,
        config.postgres_host,
    )
    await dbm.db_engine.dispose()
    engine = create_async_engine(pg_url)
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text(f"DROP DATABASE {dbm.core_db.name}"))


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
                try:
                    await es_client.delete_by_query(
                        index=db_name, query={"match_all": {}}, refresh=True
                    )
                    await es_client.delete_by_query(
                        index=f"{db_name}_entities",
                        query={"match_all": {}},
                        refresh=True,
                    )
                except elasticsearch.NotFoundError:
                    # The index has been deleted. As an index with the same name
                    # may be created and could lead to a conflict since it may be
                    # not yet available, we let this index marked as used.
                    pass
                else:
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
