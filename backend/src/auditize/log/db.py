from functools import partial
from typing import Awaitable, Callable, Iterable, cast
from uuid import UUID

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
        return ((1, self.apply_v1),)

    async def apply_v1(self):
        config = get_config()

        db = cast(LogDatabase, self.db)

        # Log collection indexes
        if not config.test_mode:
            await db.logs.create_index({"saved_at": -1})
            await db.logs.create_index("action.type")
            await db.logs.create_index("action.category")
            await db.logs.create_index({"source.name": 1, "source.value": 1})
            await db.logs.create_index("actor.ref")
            await db.logs.create_index("actor.name")
            await db.logs.create_index({"actor.extra.name": 1, "actor.extra.value": 1})
            await db.logs.create_index("resource.type")
            await db.logs.create_index("resource.ref")
            await db.logs.create_index("resource.name")
            await db.logs.create_index(
                {"resource.extra.name": 1, "resource.extra.value": 1}
            )
            await db.logs.create_index({"details.name": 1, "details.value": 1})
            await db.logs.create_index("tags.type")
            await db.logs.create_index("tags.ref")
            await db.logs.create_index("entity_path.ref")

        # Consolidated data indexes
        if not config.test_mode:
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
