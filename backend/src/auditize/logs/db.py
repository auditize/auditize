from functools import partial

from aiocache import Cache
from icecream import ic
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from auditize.database import BaseDatabase, Collection, DatabaseManager
from auditize.exceptions import PermissionDenied
from auditize.repos.models import RepoStatus


class LogDatabase(BaseDatabase):
    def __init__(self, name: str, client: AsyncIOMotorClient):
        super().__init__(name, client)
        self._cache = Cache(Cache.MEMORY)

    async def consolidate_data(
        self, collection: AsyncIOMotorCollection, data: dict[str, str]
    ):
        cache_key = "%s:%s" % (
            collection.name,
            ":".join(val or "" for val in data.values()),
        )
        if await self._cache.exists(cache_key):
            return
        ic(f"storing {collection.name!r} {data!r}")
        result = await collection.update_one(data, {"$set": {}}, upsert=True)
        await self._cache.set(cache_key, result)

    # Collections
    logs = Collection("logs")
    log_actions = Collection("log_actions")
    log_source_fields = Collection("log_source_fields")
    log_actor_types = Collection("log_actor_types")
    log_actor_extra_fields = Collection("log_actor_extra_fields")
    log_resource_types = Collection("log_resource_types")
    log_resource_extra_fields = Collection("log_resource_extra_fields")
    log_detail_fields = Collection("log_detail_fields")
    log_tag_types = Collection("log_tag_types")
    log_attachment_types = Collection("log_attachment_types")
    log_attachment_mime_types = Collection("log_attachment_mime_types")
    log_nodes = Collection("log_nodes")


def get_log_db_name(dbm: DatabaseManager, repo_id: str) -> str:
    return f"{dbm.name_prefix}_repo_{repo_id}"


async def _get_log_db(
    dbm: DatabaseManager, repo_id: str, statuses: list[RepoStatus]
) -> LogDatabase:
    from auditize.repos.service import get_repo  # avoid circular import

    repo = await get_repo(dbm, repo_id)
    if statuses:
        if repo.status not in statuses:
            # NB: we could also raise a ConstraintViolation, to be discussed
            raise PermissionDenied(
                "The repository status does not allow the requested operation"
            )

    return LogDatabase(get_log_db_name(dbm, repo_id), dbm.client)


get_log_db_for_reading = partial(
    _get_log_db, statuses=[RepoStatus.enabled, RepoStatus.readonly]
)

get_log_db_for_writing = partial(_get_log_db, statuses=[RepoStatus.enabled])

get_log_db_for_config = partial(_get_log_db, statuses=None)
