import os
import random

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from auditize.config import get_config
from auditize.database import DatabaseManager, init_dbm
from auditize.database.dbm import migrate_database
from auditize.database.sql.models import SqlModel
from auditize.log.index import create_index


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
    await dbm.db_engine.dispose()
    engine = create_async_engine(config.get_db_url("postgres"))
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
            await create_index(db_name)
            self._cache[db_name] = True
            return db_name

    async def release(self):
        for db_name, is_used in self._cache.items():
            if is_used:
                await self.dbm.elastic_client.delete_by_query(
                    index=f"{db_name}_write", query={"match_all": {}}, refresh=True
                )
                self._cache[db_name] = False
