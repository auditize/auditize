import os
import random

import elasticsearch
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from auditize.config import get_config
from auditize.database import DatabaseManager, init_dbm
from auditize.database.dbm import migrate_database
from auditize.database.sql.models import SqlModel
from auditize.log.service import create_index


def setup_test_dbm() -> DatabaseManager:
    db_name = "test_%04d" % int(random.random() * 10000)
    try:
        db_name += "_" + os.environ["PYTEST_XDIST_WORKER"]
    except KeyError:
        pass
    config = get_config()
    config.db_name = db_name
    return init_dbm(force_init=True, debug=False)


async def teardown_test_dbm(dbm: DatabaseManager):
    for index_name in await dbm.elastic_client.indices.get_alias(index=dbm.name + "*"):
        if index_name.startswith(dbm.name):
            await dbm.elastic_client.indices.delete(index=index_name)


async def create_pg_db(dbm: DatabaseManager):
    config = get_config()
    pg_url = config.get_db_url("postgres")
    engine = create_async_engine(pg_url)
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text(f"CREATE DATABASE {dbm.name}"))

    await migrate_database()


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
        config.postgres_password,
        config.postgres_host,
    )
    await dbm.db_engine.dispose()
    engine = create_async_engine(pg_url)
    async with engine.connect() as conn:
        conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
        await conn.execute(text(f"DROP DATABASE {dbm.name}"))


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
            db_name = f"{self.dbm.name}_logs_{len(self._cache)}"
            await create_index(self.dbm.elastic_client, db_name)
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
                except elasticsearch.NotFoundError:
                    # The index has been deleted. As an index with the same name
                    # may be created and could lead to a conflict since it may be
                    # not yet available, we let this index marked as used.
                    pass
                else:
                    self._cache[db_name] = False
