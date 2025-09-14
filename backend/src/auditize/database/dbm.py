from contextlib import asynccontextmanager
from typing import Self

from elasticsearch import AsyncElasticsearch
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from auditize.config import get_config
from auditize.database.elastic import get_elastic_client

_NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
}


class SqlModel(DeclarativeBase):
    metadata = MetaData(naming_convention=_NAMING_CONVENTION)


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
            elastic_client=get_elastic_client(),
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
