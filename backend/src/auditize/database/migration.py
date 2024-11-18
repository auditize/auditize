import socket
from collections.abc import Awaitable
from typing import Callable, Iterable

from pymongo.errors import DuplicateKeyError

from auditize.database.database import Database
from auditize.exceptions import AuditizeException, MigrationLocked
from auditize.helpers.datetime import now


async def acquire_migration_lock(db: Database):
    collection = db.get_collection("migration_lock")
    try:
        await collection.insert_one({"_id": "lock"})
    except DuplicateKeyError:
        raise MigrationLocked()


async def release_migration_lock(db: Database):
    await db.db.drop_collection("migration_lock")


class Migrator:
    def __init__(self, db: Database):
        self.db = db
        self.collection = db.get_collection("migrations")

    async def mark_migration_as_started(self, version: int):
        await self.collection.insert_one(
            {"version": version, "started_at": now(), "host": socket.gethostname()}
        )

    async def mark_migration_as_finished(self, version: int):
        result = await self.collection.update_one(
            {"version": version, "finished_at": {"$exists": False}},
            update={"$set": {"finished_at": now()}},
        )
        if result.modified_count == 0:
            raise AuditizeException(
                f"When marking migration version {version} as finished, could not find "
                f"corresponding pending version in {self.db.name}.{self.collection.name}"
            )

    async def get_current_version(self) -> int:
        results = await self.collection.find(
            {"finished_at": {"$exists": True}}, sort={"version": -1}, limit=1
        ).to_list(None)
        if results:
            return results[0]["version"]

        collection_names = [
            name
            for name in await self.db.db.list_collection_names()
            if name != "migrations"
        ]
        if len(collection_names) != 0:
            # there are already some collections, meaning that the database already exists, that's version 1
            return 1
        else:
            # the database is empty, that's version 0
            return 0

    def get_migrations(self) -> Iterable[tuple[int, Callable[[], Awaitable]]]:
        raise NotImplementedError()

    async def get_applicable_migrations(self, target_version: int = None):
        current_version = await self.get_current_version()
        for migration_version, migration in sorted(
            self.get_migrations(), key=lambda item: item[0]
        ):
            if migration_version > current_version:
                if target_version and migration_version > target_version:
                    break
                yield migration_version, migration

    async def apply_migrations(self, target_version: int = None):
        async for migration_version, migration in self.get_applicable_migrations(
            target_version
        ):
            print(
                f"Database {self.db.name!r}: migration version {migration_version} started..."
            )
            await self.mark_migration_as_started(migration_version)
            await migration()
            await self.mark_migration_as_finished(migration_version)
            print(
                f"Database {self.db.name!r}: migration version {migration_version} finished"
            )
