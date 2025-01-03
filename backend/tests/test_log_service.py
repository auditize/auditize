import uuid
from datetime import datetime, timedelta
from uuid import UUID

import callee
import pytest
from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.exceptions import InvalidPaginationCursor
from auditize.log.models import CustomField, Log
from auditize.log.service import (
    LogService,
    _LogsPaginationCursor,
)
from conftest import RepoBuilder
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.log import PreparedLog
from helpers.repo import PreparedRepo

pytestmark = pytest.mark.anyio


def make_log_data(**extra) -> Log:
    """
    By default, the log data is minimal viable.
    """

    kwargs = {
        "action": Log.Action(type="login", category="authentication"),
        "actor": Log.Actor(type="user", ref="user:123", name="User 123"),
        "resource": Log.Resource(ref="core", type="module", name="Core Module"),
        "tags": [Log.Tag(type="simple_tag")],
        "entity_path": [Log.Entity(ref="1", name="Customer 1")],
        **extra,
    }

    return Log(**kwargs)


async def test_save_log_db_shape(repo: PreparedRepo):
    log = make_log_data()
    log_service = await LogService.for_writing(UUID(repo.id))
    log_id = await log_service.save_log(log)
    db_log = await repo.db.logs.find_one({"_id": log_id})
    assert list(db_log.keys()) == [
        "_id",
        "action",
        "saved_at",
        "source",
        "actor",
        "resource",
        "details",
        "tags",
        "attachments",
        "entity_path",
    ]
    assert list(db_log["action"].keys()) == ["type", "category"]
    assert list(db_log["actor"].keys()) == ["ref", "type", "name", "extra"]
    assert list(db_log["resource"].keys()) == ["ref", "type", "name", "extra"]
    assert list(db_log["tags"][0].keys()) == ["ref", "type", "name"]
    assert list(db_log["entity_path"][0].keys()) == ["ref", "name"]


async def assert_consolidated_data(
    collection: AsyncIOMotorCollection, expected: dict | list
):
    if isinstance(expected, dict):
        expected = [expected]

    await assert_collection(
        collection, [{"_id": callee.Any(), **item} for item in expected]
    )


async def test_save_log_lookup_tables(repo: PreparedRepo):
    log_service = await LogService.for_writing(UUID(repo.id))

    # first log
    log = make_log_data(source=[{"name": "ip", "value": "127.0.0.1"}])
    log.actor.extra.append(CustomField(name="role", value="admin"))
    log.resource.extra.append(CustomField(name="some_key", value="some_value"))
    log.details.append(CustomField(name="detail_name", value="detail_value"))
    log.tags = [Log.Tag(ref="tag_ref", type="rich_tag", name="rich_tag_name")]
    await log_service.save_log(log)
    await assert_consolidated_data(
        repo.db.log_actions, {"category": "authentication", "type": "login"}
    )
    await assert_consolidated_data(repo.db.log_source_fields, {"name": "ip"})
    await assert_consolidated_data(repo.db.log_actor_types, {"type": "user"})
    await assert_consolidated_data(repo.db.log_actor_extra_fields, {"name": "role"})
    await assert_consolidated_data(repo.db.log_resource_types, {"type": "module"})
    await assert_consolidated_data(
        repo.db.log_resource_extra_fields, {"name": "some_key"}
    )
    await assert_consolidated_data(repo.db.log_detail_fields, {"name": "detail_name"})
    await assert_consolidated_data(repo.db.log_tag_types, {"type": "rich_tag"})
    await assert_consolidated_data(
        repo.db.log_entities,
        {"parent_entity_ref": None, "ref": "1", "name": "Customer 1"},
    )

    # second log
    log = make_log_data(source=[{"name": "ip_bis", "value": "127.0.0.1"}])
    log.action.category += "_bis"
    log.actor.type += "_bis"
    log.actor.extra.append(CustomField(name="role_bis", value="admin"))
    log.resource.type += "_bis"
    log.resource.extra.append(CustomField(name="some_key_bis", value="some_value"))
    log.details.append(CustomField(name="detail_name_bis", value="detail_value_bis"))
    log.tags = [
        Log.Tag(ref="tag_ref", type="rich_tag_bis", name="rich_tag_name"),
        Log.Tag(type="simple_tag"),
    ]
    log.entity_path.append(Log.Entity(ref="1:1", name="Entity A"))
    log_id = await log_service.save_log(log)
    await log_service.save_log_attachment(
        log_id,
        Log.Attachment(
            name="file.txt",
            type="text",
            mime_type="text/plain",
            data=b"hello",
        ),
    )
    await assert_consolidated_data(
        repo.db.log_actions,
        [
            {"category": "authentication", "type": "login"},
            {"category": "authentication_bis", "type": "login"},
        ],
    )
    await assert_consolidated_data(
        repo.db.log_source_fields, [{"name": "ip"}, {"name": "ip_bis"}]
    )
    await assert_consolidated_data(
        repo.db.log_actor_types, [{"type": "user"}, {"type": "user_bis"}]
    )
    await assert_consolidated_data(
        repo.db.log_actor_extra_fields, [{"name": "role"}, {"name": "role_bis"}]
    )
    await assert_consolidated_data(
        repo.db.log_resource_types, [{"type": "module"}, {"type": "module_bis"}]
    )
    await assert_consolidated_data(
        repo.db.log_resource_extra_fields,
        [{"name": "some_key"}, {"name": "some_key_bis"}],
    )
    await assert_consolidated_data(
        repo.db.log_detail_fields,
        [
            {"name": "detail_name"},
            {"name": "detail_name_bis"},
        ],
    )
    await assert_consolidated_data(
        repo.db.log_tag_types,
        [{"type": "rich_tag"}, {"type": "rich_tag_bis"}, {"type": "simple_tag"}],
    )
    await assert_consolidated_data(
        repo.db.log_attachment_types,
        [{"type": "text"}],
    )
    await assert_consolidated_data(
        repo.db.log_attachment_mime_types,
        [{"mime_type": "text/plain"}],
    )
    await assert_consolidated_data(
        repo.db.log_entities,
        [
            {"parent_entity_ref": None, "ref": "1", "name": "Customer 1"},
            {"parent_entity_ref": "1", "ref": "1:1", "name": "Entity A"},
        ],
    )


async def test_log_retention_period_disabled(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=3650)
    )
    await LogService.apply_log_retention_period()
    assert await repo.db.logs.count_documents({}) == 1


async def test_log_retention_period_enabled(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    # we test with repos:
    # - repo_1 with retention period and 1 log that must be deleted and 1 log that must be kept
    # - repo_2 without retention period and 2 logs that must be kept

    repo_1 = await repo_builder({"retention_period": 30})
    repo_1_log_1 = await repo_1.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=31)
    )
    repo_1_log_2 = await repo_1.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=29)
    )

    repo_2 = await repo_builder({})
    repo_2_log_1 = await repo_2.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=31)
    )
    repo_2_log_2 = await repo_2.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=29)
    )

    await LogService.apply_log_retention_period()

    assert await repo_1.db.logs.count_documents({}) == 1
    assert await repo_1.db.logs.find_one({"_id": UUID(repo_1_log_2.id)}) is not None

    assert await repo_2.db.logs.count_documents({}) == 2


async def test_log_retention_period_purge_consolidated_data(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo = await repo_builder({"retention_period": 30})
    log_1 = await repo.create_log(
        superadmin_client,
        data=PreparedLog.prepare_data(
            {
                "action": {"category": "category", "type": "action-type-to-be-kept"},
                "source": [{"name": "source-field-to-be-kept", "value": "value"}],
                "actor": {
                    "name": "some actor",
                    "ref": "actor:123",
                    "type": "actor-type-to-be-kept",
                    "extra": [
                        {"name": "actor-extra-field-to-be-kept", "value": "value"}
                    ],
                },
                "resource": {
                    "name": "some resource",
                    "ref": "resource:123",
                    "type": "resource-type-to-be-kept",
                    "extra": [
                        {"name": "resource-extra-field-to-be-kept", "value": "value"}
                    ],
                },
                "tags": [{"type": "tag-type-to-be-kept"}],
                "details": [{"name": "detail-field-to-be-kept", "value": "value"}],
            }
        ),
        saved_at=datetime.now() - timedelta(days=10),
    )
    await log_1.upload_attachment(
        superadmin_client,
        name="file.txt",
        data=b"hello",
        type="attachment-type-to-be-kept",
        mime_type="mime-type/to-be-kept",
    )
    log_2 = await repo.create_log(
        superadmin_client,
        data=PreparedLog.prepare_data(
            {
                "action": {"category": "category", "type": "action-type-to-be-purged"},
                "source": [{"name": "source-field-to-be-purged", "value": "value"}],
                "actor": {
                    "name": "some other actor",
                    "ref": "actor:456",
                    "type": "actor-type-to-be-purged",
                    "extra": [
                        {"name": "actor-extra-field-to-be-purged", "value": "value"}
                    ],
                },
                "resource": {
                    "name": "some other resource",
                    "ref": "resource:456",
                    "type": "resource-type-to-be-purged",
                    "extra": [
                        {"name": "resource-extra-field-to-be-purged", "value": "value"}
                    ],
                },
                "tags": [{"type": "tag-type-to-be-purged"}],
                "details": [{"name": "detail-field-to-be-purged", "value": "value"}],
            }
        ),
        saved_at=datetime.now() - timedelta(days=40),
    )
    await log_2.upload_attachment(
        superadmin_client,
        name="file.txt",
        data=b"hello",
        type="attachment-type-to-be-purged",
        mime_type="mime-type/to-be-purged",
    )

    await LogService.apply_log_retention_period()

    await assert_consolidated_data(
        repo.db.log_actions,
        [{"category": "category", "type": "action-type-to-be-kept"}],
    )
    await assert_consolidated_data(
        repo.db.log_source_fields, [{"name": "source-field-to-be-kept"}]
    )
    await assert_consolidated_data(
        repo.db.log_actor_types, [{"type": "actor-type-to-be-kept"}]
    )
    await assert_consolidated_data(
        repo.db.log_actor_extra_fields,
        [{"name": "actor-extra-field-to-be-kept"}],
    )
    await assert_consolidated_data(
        repo.db.log_resource_types, [{"type": "resource-type-to-be-kept"}]
    )
    await assert_consolidated_data(
        repo.db.log_resource_extra_fields,
        [{"name": "resource-extra-field-to-be-kept"}],
    )
    await assert_consolidated_data(
        repo.db.log_tag_types, [{"type": "tag-type-to-be-kept"}]
    )
    await assert_consolidated_data(
        repo.db.log_detail_fields, [{"name": "detail-field-to-be-kept"}]
    )
    await assert_consolidated_data(
        repo.db.log_attachment_types,
        [{"type": "attachment-type-to-be-kept"}],
    )
    await assert_consolidated_data(
        repo.db.log_attachment_mime_types,
        [{"mime_type": "mime-type/to-be-kept"}],
    )


async def test_log_retention_period_purge_log_entities_1(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo = await repo_builder({"retention_period": 30})
    # We have the following log entity hierarchy:
    # - A
    #   - AA
    #     - AAA
    #   - AB
    #     - ABA
    #   - AC
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AA", "AAA"],
        saved_at=datetime.now() - timedelta(days=40),
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AB", "ABA"],
        saved_at=datetime.now() - timedelta(days=40),
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AB"],
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AC"],
    )

    await LogService.apply_log_retention_period()

    await assert_consolidated_data(
        repo.db.log_entities,
        [
            {"_id": callee.Any(), "parent_entity_ref": None, "ref": "A", "name": "A"},
            {"_id": callee.Any(), "parent_entity_ref": "A", "ref": "AB", "name": "AB"},
            {"_id": callee.Any(), "parent_entity_ref": "A", "ref": "AC", "name": "AC"},
        ],
    )


async def test_log_retention_period_purge_log_entities_2(
    superadmin_client: HttpTestHelper,
    repo_builder: RepoBuilder,
):
    repo = await repo_builder({"retention_period": 30})
    # We have the following log entity hierarchy:
    # - A
    #   - AA
    #   - AB
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AA"],
        saved_at=datetime.now() - timedelta(days=40),
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AB"],
        saved_at=datetime.now() - timedelta(days=40),
    )

    await LogService.apply_log_retention_period()

    await assert_consolidated_data(
        repo.db.log_entities,
        [],
    )


def test_pagination_cursor():
    # build initial cursor
    obj_id = uuid.UUID("cc12c9bb-0b33-43cd-a410-e3f9c848a62b")
    date = datetime.fromisoformat("2021-07-19T00:00:00Z")
    cursor = _LogsPaginationCursor(id=obj_id, date=date)

    # test cursor serialization
    serialized = cursor.serialize()
    assert type(serialized) is str

    # test cursor deserialization
    new_cursor = _LogsPaginationCursor.load(serialized)
    assert new_cursor.id == obj_id
    assert new_cursor.date == date


def test_pagination_cursor_invalid_string():
    with pytest.raises(InvalidPaginationCursor):
        _LogsPaginationCursor.load("invalid_cursor_string")
