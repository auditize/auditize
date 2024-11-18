from typing import Awaitable, Callable, Iterable, cast

import certifi
from motor.motor_asyncio import (
    AsyncIOMotorClient,
)

from auditize.config import get_config
from auditize.database.database import Collection, Database
from auditize.database.migration import Migrator


class CoreDatabase(Database):
    repos = Collection("repos")
    log_i18n_profiles = Collection("log_i18n_profiles")
    users = Collection("users")
    apikeys = Collection("apikeys")
    log_filters = Collection("log_filters")


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


class _CoreDbMigrator(Migrator):
    def get_migrations(self) -> Iterable[tuple[int, Callable[[], Awaitable]]]:
        return ((1, self.apply_v1),)

    async def apply_v1(self):
        db = cast(CoreDatabase, self.db)

        # Unique indexes
        await db.repos.create_index("name", unique=True)
        await db.users.create_index("email", unique=True)
        await db.apikeys.create_index("name", unique=True)
        await db.log_i18n_profiles.create_index("name", unique=True)
        await db.log_filters.create_index("name", unique=True)

        # Text indexes
        await db.repos.create_index({"name": "text"})
        await db.users.create_index(
            {"first_name": "text", "last_name": "text", "email": "text"}
        )
        await db.apikeys.create_index({"name": "text"})
        await db.log_i18n_profiles.create_index({"name": "text"})
        await db.log_filters.create_index({"name": "text"})


async def migrate_core_db(core_db=None):
    if not core_db:
        core_db = get_core_db()
    migrator = _CoreDbMigrator(core_db)
    await migrator.apply_migrations()
