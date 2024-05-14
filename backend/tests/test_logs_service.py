import callee
import pytest
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.database import DatabaseManager
from auditize.logs.models import ExtraInfoField, Log
from auditize.logs.service import save_log
from helpers.database import assert_collection
from helpers.repos import PreparedRepo

pytestmark = pytest.mark.anyio


def make_log_data(**extra) -> Log:
    """
    By default, the log data is minimal viable.
    """

    kwargs = {
        "action": Log.Action(type="login", category="authentication"),
        "actor": Log.Actor(type="user", ref="user:123", name="User 123"),
        "resource": Log.Resource(type="module", id="core", name="Core Module"),
        "tags": [Log.Tag(id="simple_tag")],
        "node_path": [Log.Node(ref="1", name="Customer 1")],
        **extra,
    }

    return Log(**kwargs)


async def test_save_log_db_shape(dbm: DatabaseManager, repo: PreparedRepo):
    log = make_log_data()
    log_id = await save_log(dbm, repo.id, log)
    db_log = await repo.db.logs.find_one({"_id": ObjectId(log_id)})
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
        "node_path",
    ]
    assert list(db_log["action"].keys()) == ["type", "category"]
    assert list(db_log["actor"].keys()) == ["type", "ref", "name", "extra"]
    assert list(db_log["resource"].keys()) == ["type", "id", "name", "extra"]
    assert list(db_log["tags"][0].keys()) == ["id", "category", "name"]
    assert list(db_log["node_path"][0].keys()) == ["ref", "name"]


async def assert_consolidated_data(
    collection: AsyncIOMotorCollection, expected: dict | list
):
    if isinstance(expected, dict):
        expected = [expected]

    await assert_collection(
        collection, [{"_id": callee.Any(), **item} for item in expected]
    )


async def test_save_log_lookup_tables(dbm: DatabaseManager, repo: PreparedRepo):
    # first log
    log = make_log_data(source={"ip": "127.0.0.1"})
    log.actor.extra.append(ExtraInfoField(name="role", value="admin"))
    log.resource.extra = {"some_key": "some_value"}
    log.details = {"level1": {"level2": "value"}}
    log.tags = [Log.Tag(id="tag_id", category="rich_tag", name="rich_tag_name")]
    await save_log(dbm, repo.id, log)
    await assert_consolidated_data(
        repo.db.log_actions, {"category": "authentication", "type": "login"}
    )
    await assert_consolidated_data(repo.db.log_source_keys, {"key": "ip"})
    await assert_consolidated_data(repo.db.log_actor_types, {"type": "user"})
    await assert_consolidated_data(repo.db.log_actor_extra_fields, {"name": "role"})
    await assert_consolidated_data(repo.db.log_resource_types, {"type": "module"})
    await assert_consolidated_data(repo.db.log_resource_extra_keys, {"key": "some_key"})
    await assert_consolidated_data(
        repo.db.log_detail_keys, {"level1_key": "level1", "level2_key": "level2"}
    )
    await assert_consolidated_data(repo.db.log_tag_categories, {"category": "rich_tag"})
    await assert_consolidated_data(
        repo.db.log_nodes, {"parent_node_ref": None, "ref": "1", "name": "Customer 1"}
    )

    # second log
    log = make_log_data(source={"ip_bis": "127.0.0.1"})
    log.action.category += "_bis"
    log.actor.type += "_bis"
    log.actor.extra.append(ExtraInfoField(name="role_bis", value="admin"))
    log.resource.type += "_bis"
    log.resource.extra = {"some_key_bis": "some_value"}
    log.details = {"level1_bis": {"level2_bis": "value"}}
    log.tags = [
        Log.Tag(id="tag_id", category="rich_tag_bis", name="rich_tag_name"),
        Log.Tag(id="simple_tag"),
    ]
    log.node_path.append(Log.Node(ref="1:1", name="Entity A"))
    await save_log(dbm, repo.id, log)
    await assert_consolidated_data(
        repo.db.log_actions,
        [
            {"category": "authentication", "type": "login"},
            {"category": "authentication_bis", "type": "login"},
        ],
    )
    await assert_consolidated_data(
        repo.db.log_source_keys, [{"key": "ip"}, {"key": "ip_bis"}]
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
        repo.db.log_resource_extra_keys, [{"key": "some_key"}, {"key": "some_key_bis"}]
    )
    await assert_consolidated_data(
        repo.db.log_detail_keys,
        [
            {"level1_key": "level1", "level2_key": "level2"},
            {"level1_key": "level1_bis", "level2_key": "level2_bis"},
        ],
    )
    await assert_consolidated_data(
        repo.db.log_tag_categories,
        [{"category": "rich_tag"}, {"category": "rich_tag_bis"}],
    )
    await assert_consolidated_data(
        repo.db.log_nodes,
        [
            {"parent_node_ref": None, "ref": "1", "name": "Customer 1"},
            {"parent_node_ref": "1", "ref": "1:1", "name": "Entity A"},
        ],
    )
