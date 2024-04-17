import random

from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId

import callee

from auditize.main import app
from auditize.repos.models import Repo
from auditize.repos.service import create_repo
from auditize.common.mongo import DatabaseManager, get_dbm, RepoDatabase

from .http import HttpTestHelper

# A valid ObjectId, but not existing in the database
UNKNOWN_LOG_ID = "65fab045f097fe0b9b664c99"


def setup_test_dbm():
    test_dbm = DatabaseManager.spawn(base_name="test_%04d" % int(random.random() * 10000))
    app.dependency_overrides[get_dbm] = lambda: test_dbm
    return test_dbm


async def teardown_test_dbm(test_dbm):
    app.dependency_overrides[get_dbm] = get_dbm

    # Drop repos databases and core database
    async for repo in test_dbm.core_db.repos.find({}):
        await test_dbm.client.drop_database(test_dbm.get_repo_db_name(repo["_id"]))
    await test_dbm.core_db.client.drop_database(test_dbm.core_db.name)


class RepoTest:
    def __init__(self, id: str, db: RepoDatabase):
        self.id = id
        self.db = db

    @classmethod
    async def create(cls, dbm: DatabaseManager):
        repo_id = await create_repo(dbm, Repo(name="logs"))
        repo_db = dbm.get_repo_db(repo_id)
        return cls(repo_id, repo_db)


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected


async def do_test_page_pagination_common_scenarios(client: HttpTestHelper, path: str, data: list):
    """
    This function assumes that for the given path (with possible query string), the total number of items is 5.
    """
    # first test, without pagination parameters
    resp = await client.assert_get(path)
    assert resp.json() == {
        "data": data,
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 5,
            "total_pages": 1
        }
    }

    # second test, with pagination parameters
    resp = await client.assert_get(path, params={"page": 2, "page_size": 2})
    assert resp.json() == {
        "data": data[2:4],
        "pagination": {
            "page": 2,
            "page_size": 2,
            "total": 5,
            "total_pages": 3
        }
    }


async def do_test_page_pagination_empty_data(client: HttpTestHelper, path: str):
    resp = await client.assert_get(path)
    assert resp.json() == {
        "data": [],
        "pagination": {
            "page": 1,
            "page_size": 10,
            "total": 0,
            "total_pages": 0
        }
    }


def make_log_data(extra=None) -> dict:
    """
    By default, the log data is minimal viable.
    """

    extra = extra or {}

    return {
        "event": {
            "name": "user_login",
            "category": "authentication",
        },
        "node_path": [
            {
                "id": "1",
                "name": "Customer 1"
            }
        ],
        **extra
    }


def make_expected_log_data_for_api(actual):
    expected = {
        "source": {},
        "actor": None,
        "resource": None,
        "details": {},
        "tags": [],
        "attachments": [],
        **actual,
        "saved_at": callee.Regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
    }
    for tag in expected["tags"]:
        tag.setdefault("category", None)
        tag.setdefault("name", None)
    if expected["actor"]:
        expected["actor"].setdefault("extra", {})
    if expected["resource"]:
        expected["resource"].setdefault("extra", {})
    return expected


async def assert_create_log(client: HttpTestHelper, repo_id: str, log: dict, expected_status_code=201):
    resp = await client.assert_post(f"/repos/{repo_id}/logs", json=log, expected_status_code=expected_status_code)
    if expected_status_code == 201:
        assert "id" in resp.json()
    return resp


async def prepare_log(client: HttpTestHelper, repo_id: str, log: dict = None):
    resp = await assert_create_log(client, repo_id, log or make_log_data())
    return resp.json()["id"]


def alter_log_saved_at(db: RepoDatabase, log_id, new_saved_at):
    db.logs.update_one({"_id": ObjectId(log_id)}, {"$set": {"saved_at": new_saved_at}})
