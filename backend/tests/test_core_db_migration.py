from auditize.database import CoreDatabase, Database, migrate_core_db
from helpers.database import assert_db_indexes

CORE_DB_INDEXES = {
    "repos": ("name_1", "name_text"),
    "users": ("email_1", "first_name_text_last_name_text_email_text"),
    "apikeys": ("name_1", "name_text"),
    "log_i18n_profiles": ("name_1", "name_text"),
    "log_filters": ("name_1", "name_text"),
    "migrations": (),
}


async def test_core_db_migration_from_v0(tmp_db: Database):
    core_db = CoreDatabase(tmp_db.name, tmp_db.client)
    await migrate_core_db(core_db)
    await assert_db_indexes(core_db, CORE_DB_INDEXES)
