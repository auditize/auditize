from typing import Awaitable, Callable, Iterable, cast

from auditize.database.database import Collection, Database
from auditize.database.migration import Migrator


class CoreDatabase(Database):
    repos = Collection("repos")
    log_i18n_profiles = Collection("log_i18n_profiles")
    users = Collection("users")
    apikeys = Collection("apikeys")
    log_filters = Collection("log_filters")


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


async def migrate_core_db(core_db):
    migrator = _CoreDbMigrator(core_db)
    await migrator.apply_migrations()
