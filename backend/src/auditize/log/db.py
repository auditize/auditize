from functools import partial
from uuid import UUID, uuid4

from aiocache import Cache
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from auditize.config import get_config
from auditize.database import BaseDatabase, Collection, get_dbm
from auditize.exceptions import PermissionDenied
from auditize.repo.models import Repo, RepoStatus


class LogDatabase(BaseDatabase):
    def __init__(self, name: str, client: AsyncIOMotorClient):
        super().__init__(name, client)
        self._cache = Cache(Cache.MEMORY)

    async def consolidate_data(
        self,
        collection: AsyncIOMotorCollection,
        data: dict[str, str],
        update: dict[str, str] = None,
    ):
        if update is None:
            update = {}
        cache_key = "%s:%s" % (
            collection.name,
            ":".join(val or "" for val in {**data, **update}.values()),
        )
        if await self._cache.exists(cache_key):
            return
        result = await collection.update_one(
            data,
            {"$set": update, "$setOnInsert": {"_id": uuid4()}},
            upsert=True,
        )
        await self._cache.set(cache_key, result)

    async def setup(self):
        config = get_config()

        # Log collection indexes
        if not config.test_mode:
            await self.logs.create_index({"saved_at": -1})
            await self.logs.create_index("action.type")
            await self.logs.create_index("action.category")
            await self.logs.create_index({"source.name": 1, "source.value": 1})
            await self.logs.create_index("actor.ref")
            await self.logs.create_index("actor.name")
            await self.logs.create_index(
                {"actor.extra.name": 1, "actor.extra.value": 1}
            )
            await self.logs.create_index("resource.type")
            await self.logs.create_index("resource.ref")
            await self.logs.create_index("resource.name")
            await self.logs.create_index(
                {"resource.extra.name": 1, "resource.extra.value": 1}
            )
            await self.logs.create_index({"details.name": 1, "details.value": 1})
            await self.logs.create_index("tags.type")
            await self.logs.create_index("tags.ref")
            await self.logs.create_index("entity_path.ref")

        # Consolidated data indexes
        if not config.test_mode:
            await self.log_actions.create_index("type")
            await self.log_actions.create_index("category")
        await self.log_source_fields.create_index("name", unique=True)
        await self.log_actor_types.create_index("type", unique=True)
        await self.log_actor_extra_fields.create_index("name", unique=True)
        await self.log_resource_types.create_index("type", unique=True)
        await self.log_resource_extra_fields.create_index("name", unique=True)
        await self.log_detail_fields.create_index("name", unique=True)
        await self.log_tag_types.create_index("type", unique=True)
        await self.log_attachment_types.create_index("type", unique=True)
        await self.log_attachment_mime_types.create_index("mime_type", unique=True)
        await self.log_entities.create_index("ref", unique=True)

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
    log_entities = Collection("log_entities")


async def _get_log_db(repo: UUID | Repo, statuses: list[RepoStatus]) -> LogDatabase:
    from auditize.repo.service import get_repo  # avoid circular import

    if type(repo) is UUID:
        repo = await get_repo(repo)

    if statuses:
        if repo.status not in statuses:
            # NB: we could also raise a ConstraintViolation, to be discussed
            raise PermissionDenied(
                "The repository status does not allow the requested operation"
            )

    return LogDatabase(repo.log_db_name, get_dbm().client)


get_log_db_for_reading = partial(
    _get_log_db, statuses=[RepoStatus.enabled, RepoStatus.readonly]
)

get_log_db_for_writing = partial(_get_log_db, statuses=[RepoStatus.enabled])

get_log_db_for_config = partial(_get_log_db, statuses=None)

get_log_db_for_maintenance = partial(_get_log_db, statuses=None)
