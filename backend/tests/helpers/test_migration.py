import pytest

from auditize.database import Migrator, acquire_migration_lock, release_migration_lock
from auditize.exceptions import MigrationLocked


async def test_acquire_migration_lock(tmp_db):
    await acquire_migration_lock(tmp_db)
    with pytest.raises(MigrationLocked):
        await acquire_migration_lock(tmp_db)


async def test_acquire_migration_release(tmp_db):
    await acquire_migration_lock(tmp_db)
    await release_migration_lock(tmp_db)
    await acquire_migration_lock(tmp_db)


async def test_get_current_version_0(tmp_db):
    migration = Migrator(tmp_db)
    assert await migration.get_current_version() == 0


async def test_get_current_version_1(tmp_db):
    await tmp_db.db.get_collection("some_collection").create_index("name")
    migrator = Migrator(tmp_db)
    assert await migrator.get_current_version() == 1


async def test_get_current_version_1_pending(tmp_db):
    migrator = Migrator(tmp_db)
    await migrator.mark_migration_as_started(1)
    assert await migrator.get_current_version() == 0


async def test_get_current_version_2(tmp_db):
    migrator = Migrator(tmp_db)
    await migrator.mark_migration_as_started(1)
    await migrator.mark_migration_as_finished(1)
    await migrator.mark_migration_as_started(2)
    await migrator.mark_migration_as_finished(2)

    assert await migrator.get_current_version() == 2


async def test_get_applicable_migrations_from_0_to_1(tmp_db):
    class TestMigrator(Migrator):
        def get_migrations(self):
            return ((1, lambda: None),)

    migrator = TestMigrator(tmp_db)
    migrations = [migration async for migration in migrator.get_applicable_migrations()]
    assert len(migrations) == 1
    assert migrations[0][0] == 1


async def test_get_applicable_migrations_from_1_to_1(tmp_db):
    class TestMigrator(Migrator):
        def get_migrations(self):
            return ((1, lambda: None),)

    migrator = TestMigrator(tmp_db)
    await migrator.mark_migration_as_started(1)
    await migrator.mark_migration_as_finished(1)
    migrations = [migration async for migration in migrator.get_applicable_migrations()]
    assert len(migrations) == 0


async def test_get_applicable_migrations_from_0_to_2(tmp_db):
    class TestMigrator(Migrator):
        def get_migrations(self):
            return (
                (1, lambda: None),
                (2, lambda: None),
            )

    migrator = TestMigrator(tmp_db)
    migrations = [migration async for migration in migrator.get_applicable_migrations()]
    assert len(migrations) == 2
    assert migrations[0][0] == 1
    assert migrations[1][0] == 2


async def test_get_applicable_migrations_from_0_to_1_target(tmp_db):
    class TestMigrator(Migrator):
        def get_migrations(self):
            return (
                (1, lambda: None),
                (2, lambda: None),
            )

    migrator = TestMigrator(tmp_db)
    migrations = [
        migration
        async for migration in migrator.get_applicable_migrations(target_version=1)
    ]
    assert len(migrations) == 1
    assert migrations[0][0] == 1


async def test_apply_migrations(tmp_db):
    class TestMigrator(Migrator):
        async def v1(self):
            await self.db.get_collection("coll_v1").create_index("name")

        async def v2(self):
            await self.db.get_collection("coll_v2").create_index("name")

        def get_migrations(self):
            return (
                (1, self.v1),
                (2, self.v2),
            )

    migrator = TestMigrator(tmp_db)
    await migrator.apply_migrations()
    assert await migrator.get_current_version() == 2
    assert list(sorted(await tmp_db.db.list_collection_names())) == [
        "coll_v1",
        "coll_v2",
        "migrations",
    ]
