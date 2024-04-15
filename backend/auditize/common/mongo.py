from datetime import timezone
from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from bson.codec_options import CodecOptions
from aiocache import Cache
from icecream import ic


class _Collection:
    def __init__(self, name):
        self.name = name

    @lru_cache
    def __get__(self, db: "Database", _) -> AsyncIOMotorCollection:
        return db.client.get_database(db.name).get_collection(
            self.name,
            codec_options=CodecOptions(
                tz_aware=True,
                tzinfo=timezone.utc
            )
        )


class _BaseDatabase:
    def __init__(self, name: str, client: AsyncIOMotorClient):
        self.name = name
        self.client = client


class RepoDatabase(_BaseDatabase):
    def __init__(self, name: str, client: AsyncIOMotorClient):
        super().__init__(name, client)
        self._cache = Cache(Cache.MEMORY)

    async def consolidate_data(self, collection: AsyncIOMotorCollection, data: dict[str, str]):
        cache_key = "%s:%s" % (collection.name, ":".join(val or "" for val in data.values()))
        if await self._cache.exists(cache_key):
            return
        ic(f"storing {collection.name!r} {data!r}")
        await collection.update_one(data, {"$set": {}}, upsert=True)
        await self._cache.set(cache_key, True)

    # Collections
    logs = _Collection("logs")
    log_events = _Collection("log_events")
    log_source_keys = _Collection("log_source_keys")
    log_actor_types = _Collection("log_actor_types")
    log_actor_extra_keys = _Collection("log_actor_extra_keys")
    log_resource_types = _Collection("log_resource_types")
    log_resource_extra_keys = _Collection("log_resource_extra_keys")
    log_detail_keys = _Collection("log_detail_keys")
    log_tag_categories = _Collection("log_tag_categories")
    log_nodes = _Collection("log_nodes")


class CoreDatabase(_BaseDatabase):
    async def setup(self):
        await self.repos.create_index("name", unique=True)

    # Collections
    repos = _Collection("repos")


_mongo_client = AsyncIOMotorClient()


class DatabaseManager:
    def __init__(self, client: AsyncIOMotorClient, base_name):
        self.client = client
        self.base_name = base_name
        self.core_db = CoreDatabase(self.base_name, client)

    @classmethod
    def spawn(cls, client: AsyncIOMotorClient = None, base_name="auditize"):
        return cls(client or _mongo_client, base_name)

    def setup(self):
        return self.core_db.setup()

    def get_repo_db_name(self, repo_id: str) -> str:
        return f"{self.base_name}_repo_{repo_id}"

    @lru_cache
    def get_repo_db(self, repo_name: str) -> RepoDatabase:
        return RepoDatabase(self.get_repo_db_name(repo_name), self.client)


_dbm = DatabaseManager.spawn(_mongo_client)


def get_dbm() -> DatabaseManager:
    return _dbm
