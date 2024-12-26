from typing import Self

import certifi
from elasticsearch import AsyncElasticsearch
from motor.motor_asyncio import AsyncIOMotorClient

from auditize.config import get_config
from auditize.database import CoreDatabase
from auditize.database.elastic import get_elastic_client


class DatabaseManager:
    _dbm: Self = None

    def __init__(self, *, core_db: CoreDatabase, elastic_client: AsyncElasticsearch):
        self.core_db: CoreDatabase = core_db
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


def get_core_db() -> CoreDatabase:
    dbm = DatabaseManager.get()
    return dbm.core_db
