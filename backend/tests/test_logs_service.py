from auditize.logs.models import Log
from auditize.logs.service import save_log, log_collection

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.anyio


async def test_save_log_db_shape(client: AsyncClient):
    log = Log(
        event=Log.Event(name="login", category="authentication"),
        actor=Log.Actor(type="user", id="user:123", name="User 123"),
        resource=Log.Resource(type="module", id="core", name="Core Module"),
        tags=[Log.Tag(id="simple_tag")],
        node_path=[Log.Node(id="1", name="Customer 1")]
    )
    log_id = await save_log(log)
    db_log = await log_collection.find_one({"_id": log_id})
    assert list(db_log.keys()) == [
        "_id", "event", "saved_at", "source", "actor", "resource", "details", "tags", "node_path"
    ]
    assert list(db_log["event"].keys()) == ["name", "category"]
    assert list(db_log["actor"].keys()) == ["type", "id", "name", "extra"]
    assert list(db_log["resource"].keys()) == ["type", "id", "name", "extra"]
    assert list(db_log["tags"][0].keys()) == ["id", "type", "name"]
    assert list(db_log["node_path"][0].keys()) == ["id", "name"]
