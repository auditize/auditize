from datetime import timezone
from functools import lru_cache

from bson.codec_options import CodecOptions
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


class Collection:
    def __init__(self, name):
        self.name = name

    @lru_cache
    def __get__(self, db: "BaseDatabase", _) -> AsyncIOMotorCollection:
        return db.db.get_collection(
            self.name, codec_options=CodecOptions(tz_aware=True, tzinfo=timezone.utc)
        )


class BaseDatabase:
    def __init__(self, name: str, client: AsyncIOMotorClient):
        self.name = name
        self.client = client

    @property
    def db(self):
        return self.client.get_database(self.name)


class CoreDatabase(BaseDatabase):
    async def setup(self):
        await self.repos.create_index("name", unique=True)
        await self.users.create_index("email", unique=True)
        await self.integrations.create_index("name", unique=True)

    # Collections
    repos = Collection("repos")
    users = Collection("users")
    integrations = Collection("integrations")


_mongo_client = AsyncIOMotorClient()


class DatabaseManager:
    def __init__(self, client: AsyncIOMotorClient, name_prefix: str):
        self.client = client
        self.name_prefix = name_prefix
        self.core_db = CoreDatabase(self.name_prefix, client)

    @classmethod
    def spawn(cls, client: AsyncIOMotorClient = None, name_prefix="auditize"):
        return cls(client or _mongo_client, name_prefix)

    def setup(self):
        return self.core_db.setup()


_dbm = DatabaseManager.spawn(_mongo_client)


def get_dbm() -> DatabaseManager:
    return _dbm
