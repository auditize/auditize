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
        await self.logi18nprofiles.create_index("name", unique=True)
        await self.log_filters.create_index("name", unique=True)

        # Text indexes
        await self.repos.create_index({"name": "text"})
        await self.users.create_index(
            {"first_name": "text", "last_name": "text", "email": "text"}
        )
        await self.apikeys.create_index({"name": "text"})
        await self.logi18nprofiles.create_index({"name": "text"})
        await self.log_filters.create_index({"name": "text"})

    # Collections
    # FIXME: naming convention (spaces vs underscores)
    repos = Collection("repos")
    logi18nprofiles = Collection("logi18nprofiles")
    users = Collection("users")
    apikeys = Collection("apikeys")
    log_filters = Collection("log_filters")


def setup_mongo_client(uri: str = None) -> AsyncIOMotorClient:
    return AsyncIOMotorClient(uri)


_mongo_client = setup_mongo_client(get_config().mongodb_uri)


class DatabaseManager:
    def __init__(self, client: AsyncIOMotorClient, name_prefix: str):
        self.client = client
        self.name_prefix = name_prefix
        self.core_db = CoreDatabase(self.name_prefix, client)

    @classmethod
    def spawn(cls, client: AsyncIOMotorClient = None, name_prefix="auditize"):
        return cls(client or _mongo_client, name_prefix)

    async def setup(self):
        # avoid circular imports
        from auditize.logs.db import get_log_db_for_maintenance
        from auditize.repo.service import get_all_repos

        await self.core_db.setup()
        for repo in await get_all_repos(self):
            log_db = await get_log_db_for_maintenance(self, repo)
            await log_db.setup()


_dbm = DatabaseManager.spawn(_mongo_client)


def get_dbm() -> DatabaseManager:
    return _dbm
