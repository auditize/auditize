import certifi
from motor.motor_asyncio import (
    AsyncIOMotorClient,
)

from auditize.config import get_config
from auditize.database.database import Collection, Database


class CoreDatabase(Database):
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


async def migrate_databases():
    # avoid circular imports
    from auditize.log.db import get_log_db_for_maintenance
    from auditize.repo.service import get_all_repos

    await get_core_db().setup()
    for repo in await get_all_repos():
        log_db = await get_log_db_for_maintenance(repo)
        await log_db.setup()
