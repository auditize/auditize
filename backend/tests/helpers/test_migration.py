import pytest

from auditize.database import acquire_migration_lock, release_migration_lock
from auditize.exceptions import MigrationLocked


async def test_acquire_migration_lock(tmp_db):
    await acquire_migration_lock(tmp_db)
    with pytest.raises(MigrationLocked):
        await acquire_migration_lock(tmp_db)


async def test_acquire_migration_release(tmp_db):
    await acquire_migration_lock(tmp_db)
    await release_migration_lock(tmp_db)
    await acquire_migration_lock(tmp_db)
