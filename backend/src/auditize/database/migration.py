from pymongo.errors import DuplicateKeyError

from auditize.database import Database
from auditize.exceptions import MigrationLocked


async def acquire_migration_lock(db: Database):
    collection = db.get_collection("migration_lock")
    try:
        await collection.insert_one({"_id": "lock"})
    except DuplicateKeyError:
        raise MigrationLocked()


async def release_migration_lock(db: Database):
    await db.db.drop_collection("migration_lock")
