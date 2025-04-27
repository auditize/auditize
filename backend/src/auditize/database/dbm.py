from typing import Generator, Self

import certifi
from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession

from auditize.config import get_config
from auditize.database import CoreDatabase
from auditize.database.elastic import get_elastic_client


class DatabaseManager:
    _dbm: Self = None

    def __init__(
        self,
        *,
        core_db: CoreDatabase,
        db_engine: AsyncEngine,
        elastic_client: AsyncElasticsearch,
    ):
        self.core_db: CoreDatabase = core_db
        self.db_engine: AsyncEngine = db_engine
        self.elastic_client: AsyncElasticsearch = elastic_client

    @classmethod
    def init(cls, name=None, *, force_init=False) -> Self:
        if not force_init and cls._dbm:
            raise Exception("DatabaseManager is already initialized")
        config = get_config()
        if not name:
            name = config.db_name
        cls._dbm = cls(
            core_db=CoreDatabase(
                name,
                AsyncIOMotorClient(
                    config.mongodb_uri,
                    tlsCAFile=certifi.where() if config.mongodb_tls else None,
                ),
            ),
            db_engine=create_async_engine(
                "postgresql+asyncpg://%s:%s@%s:5432/%s"
                % (
                    config.postgres_user,
                    config.postgres_user_password,
                    config.postgres_host,
                    config.db_name,
                )
            ),
            elastic_client=get_elastic_client(),
        )
        return cls._dbm

    @classmethod
    def get(cls) -> Self:
        if not cls._dbm:
            raise Exception("DatabaseManager is not initialized")
        return cls._dbm


def init_dbm(name=None, *, force_init=False) -> DatabaseManager:
    return DatabaseManager.init(name, force_init=force_init)


def get_dbm() -> DatabaseManager:
    return DatabaseManager.get()


def get_core_db() -> CoreDatabase:
    dbm = get_dbm()
    return dbm.core_db


def get_db_session() -> Generator[_AsyncSession, None, None]:
    dbm = get_dbm()
    with _AsyncSession(dbm.db_engine, expire_on_commit=False) as session:
        yield session
