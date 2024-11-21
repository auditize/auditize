from functools import partial
from typing import Awaitable, Callable, Iterable, cast
from uuid import UUID

from pymongo.collation import Collation

from auditize.config import get_config
from auditize.database import Collection, Database, Migrator, get_core_db
from auditize.exceptions import PermissionDenied
from auditize.repo.models import Repo, RepoStatus


class LogDatabase(Database):
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

    repo = await get_repo(repo)

    if statuses:
        if repo.status not in statuses:
            # NB: we could also raise a ConstraintViolation, to be discussed
            raise PermissionDenied(
                "The repository status does not allow the requested operation"
            )

    return LogDatabase(repo.log_db_name, get_core_db().client)


get_log_db_for_reading = partial(
    _get_log_db, statuses=[RepoStatus.enabled, RepoStatus.readonly]
)

get_log_db_for_writing = partial(_get_log_db, statuses=[RepoStatus.enabled])

get_log_db_for_config = partial(_get_log_db, statuses=None)

get_log_db_for_maintenance = partial(_get_log_db, statuses=None)


class _LogDbMigrator(Migrator):
    def get_migrations(self) -> Iterable[tuple[int, Callable[[], Awaitable]]]:
        return ((2, self.apply_v2),)

    # NB: to avoid creating a "logs" collection with initial indexes of v1 to remove them right after
    # that in v2, we directly implement a v2 that will be able to manage migration from both v0 and v1

    async def apply_v2(self):
        db = cast(LogDatabase, self.db)
        current_version = await self.get_current_version()

        ###
        # Log collection indexes
        ###

        if current_version == 1:
            await db.logs.drop_indexes()

        await db.logs.create_index({"saved_at": -1, "_id": -1})
        await db.logs.create_index({"action.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"source.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"actor.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"resource.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"details.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"tags.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"attachments.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"attachments.$**": 1, "saved_at": -1, "_id": -1})
        await db.logs.create_index({"entity_path.ref": 1, "saved_at": -1, "_id": -1})

        ###
        # Consolidated data indexes
        ###

        if current_version == 0:
            await db.log_actions.create_index("type")
            await db.log_actions.create_index("category")
            await db.log_source_fields.create_index("name", unique=True)
            await db.log_actor_types.create_index("type", unique=True)
            await db.log_actor_extra_fields.create_index("name", unique=True)
            await db.log_resource_types.create_index("type", unique=True)
            await db.log_resource_extra_fields.create_index("name", unique=True)
            await db.log_detail_fields.create_index("name", unique=True)
            await db.log_tag_types.create_index("type", unique=True)
            await db.log_attachment_types.create_index("type", unique=True)
            await db.log_attachment_mime_types.create_index("mime_type", unique=True)
            await db.log_entities.create_index("ref", unique=True)


async def migrate_log_db(log_db: LogDatabase):
    migrator = _LogDbMigrator(log_db)
    await migrator.apply_migrations()


async def migrate_all_log_dbs():
    from auditize.repo.service import get_all_repos  # avoid circular imports

    for repo in await get_all_repos():
        log_db = await get_log_db_for_maintenance(repo)
        await migrate_log_db(log_db)
