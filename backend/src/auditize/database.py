from contextlib import asynccontextmanager
from datetime import timezone
from functools import lru_cache

import certifi
from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCollection,
)

from auditize.config import get_config


class Collection:
    def __init__(self, name):
        self.name = name

    @lru_cache
    def __get__(self, db: "Database", _) -> AsyncIOMotorCollection:
        return db.db.get_collection(
            self.name,
            codec_options=CodecOptions(
                tz_aware=True,
                tzinfo=timezone.utc,
                uuid_representation=UuidRepresentation.STANDARD,
            ),
        )


class Database:
    def __init__(self, name: str, client: AsyncIOMotorClient):
        self.name = name
        self.client = client

    @property
    def db(self):
        return self.client.get_database(self.name)

    def get_collection(self, name):
        return self.db.get_collection(name)

    @asynccontextmanager
    async def transaction(self) -> AsyncIOMotorClientSession:
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session

    async def ping(self):
        await self.client.server_info()


class CoreDatabase(Database):
    async def setup(self):
        # Unique indexes
        await self.repos.create_index("name", unique=True)
        await self.users.create_index("email", unique=True)
        await self.apikeys.create_index("name", unique=True)
        await self.log_i18n_profiles.create_index("name", unique=True)
        await self.log_filters.create_index("name", unique=True)

        # Text indexes
        await self.repos.create_index({"name": "text"})
        await self.users.create_index(
            {"first_name": "text", "last_name": "text", "email": "text"}
        )
        await self.apikeys.create_index({"name": "text"})
        await self.log_i18n_profiles.create_index({"name": "text"})
        await self.log_filters.create_index({"name": "text"})

    # Collections
    repos = Collection("repos")
    log_i18n_profiles = Collection("log_i18n_profiles")
    users = Collection("users")
    apikeys = Collection("apikeys")
    log_filters = Collection("log_filters")


async def migrate_databases():
    # avoid circular imports
    from auditize.log.db import get_log_db_for_maintenance
    from auditize.repo.service import get_all_repos

    await get_core_db().setup()
    for repo in await get_all_repos():
        log_db = await get_log_db_for_maintenance(repo)
        await log_db.setup()


_core_db: CoreDatabase | None = None


def init_core_db(name="auditize", *, force_init=False) -> CoreDatabase:
    global _core_db
    if not force_init and _core_db:
        raise Exception("CoreDatabase is already initialized")
    config = get_config()
    _core_db = CoreDatabase(
        name,
        AsyncIOMotorClient(
            config.mongodb_uri,
            tlsCAFile=certifi.where() if config.mongodb_tls else None,
        ),
    )
    return _core_db


def get_core_db() -> CoreDatabase:
    if not _core_db:
        raise Exception("CoreDatabase is not initialized")
    return _core_db
