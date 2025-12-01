import asyncio
import os.path as osp
from contextlib import asynccontextmanager
from typing import Self

from alembic import command
from alembic.config import Config
from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from auditize.config import get_config
from auditize.database.elastic import init_elastic_client


class DatabaseManager:
    _dbm: Self = None

    def __init__(
        self,
        name: str,
        *,
        db_engine: AsyncEngine,
        elastic_client: AsyncElasticsearch,
    ):
        self.name: str = name
        self.db_engine: AsyncEngine = db_engine
        self.elastic_client: AsyncElasticsearch = elastic_client

    @classmethod
    def init(cls, name=None, *, force_init=False, debug=False) -> Self:
        if not force_init and cls._dbm:
            raise Exception("DatabaseManager is already initialized")
        config = get_config()
        if not name:
            name = config.db_name
        cls._dbm = cls(
            name=name,
            db_engine=create_async_engine(config.get_db_url(name), echo=debug),
            elastic_client=init_elastic_client(),
        )
        return cls._dbm

    @classmethod
    def get(cls) -> Self:
        if not cls._dbm:
            raise Exception("DatabaseManager is not initialized")
        return cls._dbm


def init_dbm(name=None, *, force_init=False, debug=False) -> DatabaseManager:
    return DatabaseManager.init(name, force_init=force_init, debug=debug)


def get_dbm() -> DatabaseManager:
    return DatabaseManager.get()


def get_elastic_client() -> AsyncElasticsearch:
    return get_dbm().elastic_client


@asynccontextmanager
async def open_db_session():
    dbm = get_dbm()
    async with AsyncSession(
        dbm.db_engine, expire_on_commit=False, autoflush=False
    ) as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


async def migrate_database():
    current_dir = osp.dirname(__file__)
    alembic_config = Config(osp.join(current_dir, "alembic.ini"))
    alembic_config.set_section_option(
        "alembic", "script_location", osp.join(current_dir, "alembic")
    )

    # This is needed because alembic run async migrations using
    # asyncio.run() later
    def upgrade_sync():
        command.upgrade(alembic_config, "head")

    await asyncio.to_thread(upgrade_sync)
