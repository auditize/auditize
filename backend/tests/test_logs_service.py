from datetime import datetime
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.logs.models import Log
from auditize.logs.service import save_log, PaginationCursor, InvalidPaginationCursor
from auditize.common.mongo import Database

import pytest

pytestmark = pytest.mark.anyio


def make_log_data(**extra) -> Log:
    """
    By default, the log data is minimal viable.
    """

    kwargs = {
        "event": Log.Event(name="login", category="authentication"),
        "actor": Log.Actor(type="user", id="user:123", name="User 123"),
        "resource": Log.Resource(type="module", id="core", name="Core Module"),
        "tags": [Log.Tag(id="simple_tag")],
        "node_path": [Log.Node(id="1", name="Customer 1")],
        **extra
    }

    return Log(**kwargs)


async def test_save_log_db_shape(db: Database):
    log = make_log_data()
    log_id = await save_log(db, log)
    db_log = await db.logs.find_one({"_id": log_id})
    assert list(db_log.keys()) == [
        "_id", "event", "saved_at", "source", "actor", "resource", "details", "tags", "attachments", "node_path"
    ]
    assert list(db_log["event"].keys()) == ["name", "category"]
    assert list(db_log["actor"].keys()) == ["type", "id", "name", "extra"]
    assert list(db_log["resource"].keys()) == ["type", "id", "name", "extra"]
    assert list(db_log["tags"][0].keys()) == ["id", "category", "name"]
    assert list(db_log["node_path"][0].keys()) == ["id", "name"]


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}, {"_id": 0}).to_list(None)
    assert results == expected


async def test_save_log_lookup_tables(db: Database):
    # first log
    log = make_log_data(source={"ip": "127.0.0.1"})
    log.actor.extra = {"role": "admin"}
    log.resource.extra = {"some_key": "some_value"}
    log.details = {"level1": {"level2": "value"}}
    log.tags = [Log.Tag(id="tag_id", category="rich_tag", name="rich_tag_name")]
    await save_log(db, log)
    await assert_collection(db.log_events, [{"category": "authentication", "name": "login"}])
    await assert_collection(db.log_source_keys, [{"key": "ip"}])
    await assert_collection(db.log_actor_types, [{"type": "user"}])
    await assert_collection(db.log_actor_extra_keys, [{"key": "role"}])
    await assert_collection(db.log_resource_types, [{"type": "module"}])
    await assert_collection(db.log_resource_extra_keys, [{"key": "some_key"}])
    await assert_collection(db.log_detail_keys, [{"level1_key": "level1", "level2_key": "level2"}])
    await assert_collection(db.log_tag_categories, [{"category": "rich_tag"}])
    await assert_collection(db.log_nodes, [{"parent_node_id": None, "id": "1", "name": "Customer 1"}])

    # second log
    log = make_log_data(source={"ip_bis": "127.0.0.1"})
    log.event.category += "_bis"
    log.actor.type += "_bis"
    log.actor.extra = {"role_bis": "admin"}
    log.resource.type += "_bis"
    log.resource.extra = {"some_key_bis": "some_value"}
    log.details = {"level1_bis": {"level2_bis": "value"}}
    log.tags = [Log.Tag(id="tag_id", category="rich_tag_bis", name="rich_tag_name"), Log.Tag(id="simple_tag")]
    log.node_path.append(Log.Node(id="1:1", name="Entity A"))
    await save_log(db, log)
    await assert_collection(
        db.log_events, [
            {"category": "authentication", "name": "login"},
            {"category": "authentication_bis", "name": "login"}
        ]
    )
    await assert_collection(
        db.log_source_keys, [
            {"key": "ip"}, {"key": "ip_bis"}
        ]
    )
    await assert_collection(
        db.log_actor_types, [
            {"type": "user"}, {"type": "user_bis"}
        ]
    )
    await assert_collection(
        db.log_actor_extra_keys, [
            {"key": "role"}, {"key": "role_bis"}
        ]
    )
    await assert_collection(
        db.log_resource_types, [
            {"type": "module"}, {"type": "module_bis"}
        ]
    )
    await assert_collection(
        db.log_resource_extra_keys, [
            {"key": "some_key"}, {"key": "some_key_bis"}
        ]
    )
    await assert_collection(db.log_detail_keys, [
        {"level1_key": "level1", "level2_key": "level2"},
        {"level1_key": "level1_bis", "level2_key": "level2_bis"}
    ]
    )
    await assert_collection(
        db.log_tag_categories, [
            {"category": "rich_tag"},
            {"category": "rich_tag_bis"}
        ]
    )
    await assert_collection(
        db.log_nodes, [
            {"parent_node_id": None, "id": "1", "name": "Customer 1"},
            {"parent_node_id": "1", "id": "1:1", "name": "Entity A"}
        ]
    )


def test_pagination_cursor():
    # build initial cursor
    log_id = ObjectId("60f3b3b3b3b3b3b3b3b3b3b3")
    date = datetime.fromisoformat("2021-07-19T00:00:00Z")
    cursor = PaginationCursor(log_id=log_id, date=date)

    # test cursor serialization
    serialized = cursor.serialize()
    assert type(serialized) is str

    # test cursor deserialization
    new_cursor = PaginationCursor.load(serialized)
    assert new_cursor.log_id == log_id
    assert new_cursor.date == date


def test_pagination_cursor_invalid_string():
    with pytest.raises(InvalidPaginationCursor):
        PaginationCursor.load("invalid_cursor_string")
