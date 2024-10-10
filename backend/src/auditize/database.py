from datetime import timezone
from functools import lru_cache

from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from auditize.config import get_config


class Collection:
    def __init__(self, name):
        self.name = name

    @lru_cache
    def __get__(self, db: "BaseDatabase", _) -> AsyncIOMotorCollection:
        return db.db.get_collection(
            self.name,
            codec_options=CodecOptions(
                tz_aware=True,
                tzinfo=timezone.utc,
                uuid_representation=UuidRepresentation.STANDARD,
            ),
        )


class BaseDatabase:
    def __init__(self, name: str, client: AsyncIOMotorClient):
        self.name = name
        self.client = client

    @property
    def db(self):
        return self.client.get_database(self.name)

    def get_collection(self, name):
        return self.db.get_collection(name)


class CoreDatabase(BaseDatabase):
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
    # FIXME: naming convention (spaces vs underscores)
    repos = Collection("repos")
    log_i18n_profiles = Collection("log_i18n_profiles")
    users = Collection("users")
    apikeys = Collection("apikeys")
    log_filters = Collection("log_filters")


class DatabaseManager:
    def __init__(self, client: AsyncIOMotorClient, name_prefix: str):
        self.client = client
        self.name_prefix = name_prefix
        self.core_db = CoreDatabase(self.name_prefix, client)

    @classmethod
    def spawn(cls, client: AsyncIOMotorClient, name_prefix="auditize"):
        return cls(client, name_prefix)

    async def setup(self):
        # avoid circular imports
        from auditize.log.db import get_log_db_for_maintenance
        from auditize.repo.service import get_all_repos

        await self.core_db.setup()
        for repo in await get_all_repos():
            log_db = await get_log_db_for_maintenance(repo)
            await log_db.setup()

    async def ping(self):
        await self.client.server_info()


_dbm: DatabaseManager | None = None


def init_dbm(name_prefix="auditize", *, force_init=False) -> DatabaseManager:
    global _dbm
    if not force_init and _dbm:
        raise Exception("DatabaseManager is already initialized")
    config = get_config()
    _dbm = DatabaseManager.spawn(
        AsyncIOMotorClient(config.mongodb_uri), name_prefix=name_prefix
    )
    return _dbm


def get_dbm() -> DatabaseManager:
    if not _dbm:
        raise Exception("DatabaseManager is not initialized")
    return _dbm
