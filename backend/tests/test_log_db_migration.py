from auditize.log.db import Database, LogDatabase, migrate_log_db
from helpers.database import assert_db_indexes

LOG_DB_INDEXES = {
    "logs": (
        "action.$**_1_saved_at_-1__id_-1",
        "actor.$**_1_saved_at_-1__id_-1",
        "attachments.$**_1_saved_at_-1__id_-1",
        "details.$**_1_saved_at_-1__id_-1",
        "entity_path.ref_1_saved_at_-1__id_-1",
        "resource.$**_1_saved_at_-1__id_-1",
        "saved_at_-1__id_-1",
        "source.$**_1_saved_at_-1__id_-1",
        "tags.$**_1_saved_at_-1__id_-1",
    ),
    "log_actions": ("type_1", "category_1"),
    "log_source_fields": ("name_1",),
    "log_actor_types": ("type_1",),
    "log_actor_extra_fields": ("name_1",),
    "log_resource_types": ("type_1",),
    "log_resource_extra_fields": ("name_1",),
    "log_detail_fields": ("name_1",),
    "log_tag_types": ("type_1",),
    "log_attachment_types": ("type_1",),
    "log_attachment_mime_types": ("mime_type_1",),
    "log_entities": ("ref_1",),
    "migrations": (),
}


async def test_log_db_migration_from_v0(tmp_db: Database):
    log_db = LogDatabase(tmp_db.name, tmp_db.client)
    await migrate_log_db(log_db)
    await assert_db_indexes(log_db, LOG_DB_INDEXES)


async def test_log_db_migration_from_v1(tmp_db: Database):
    log_db = LogDatabase(tmp_db.name, tmp_db.client)

    # Set the log db as it was prior 0.5.0

    await log_db.logs.create_index({"saved_at": -1})
    await log_db.logs.create_index("action.type")
    await log_db.logs.create_index("action.category")
    await log_db.logs.create_index({"source.name": 1, "source.value": 1})
    await log_db.logs.create_index("actor.ref")
    await log_db.logs.create_index("actor.name")
    await log_db.logs.create_index({"actor.extra.name": 1, "actor.extra.value": 1})
    await log_db.logs.create_index("resource.type")
    await log_db.logs.create_index("resource.ref")
    await log_db.logs.create_index("resource.name")
    await log_db.logs.create_index(
        {"resource.extra.name": 1, "resource.extra.value": 1}
    )
    await log_db.logs.create_index({"details.name": 1, "details.value": 1})
    await log_db.logs.create_index("tags.type")
    await log_db.logs.create_index("tags.ref")
    await log_db.logs.create_index("entity_path.ref")

    await log_db.log_actions.create_index("type")
    await log_db.log_actions.create_index("category")
    await log_db.log_source_fields.create_index("name", unique=True)
    await log_db.log_actor_types.create_index("type", unique=True)
    await log_db.log_actor_extra_fields.create_index("name", unique=True)
    await log_db.log_resource_types.create_index("type", unique=True)
    await log_db.log_resource_extra_fields.create_index("name", unique=True)
    await log_db.log_detail_fields.create_index("name", unique=True)
    await log_db.log_tag_types.create_index("type", unique=True)
    await log_db.log_attachment_types.create_index("type", unique=True)
    await log_db.log_attachment_mime_types.create_index("mime_type", unique=True)
    await log_db.log_entities.create_index("ref", unique=True)

    await migrate_log_db(log_db)
    await assert_db_indexes(log_db, LOG_DB_INDEXES)
