import random

from motor.motor_asyncio import AsyncIOMotorCollection


from auditize.main import app
from auditize.common.mongo import DatabaseManager, get_dbm

from .http import HttpTestHelper


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


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected


async def do_test_page_pagination_common_scenarios(client: HttpTestHelper, path: str, data: list):
    """
    This function assumes that for the given path (with possible query string), the total number of items is 5.
    """
    # first test, without pagination parameters
    await client.assert_get(
        path,
        expected_json={
            "data": data,
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 5,
                "total_pages": 1
            }
        }
    )

    # second test, with pagination parameters
    await client.assert_get(
        path,
        params={"page": 2, "page_size": 2},
        expected_json={
            "data": data[2:4],
            "pagination": {
                "page": 2,
                "page_size": 2,
                "total": 5,
                "total_pages": 3
            }
        }
    )


async def do_test_page_pagination_empty_data(client: HttpTestHelper, path: str):
    await client.assert_get(
        path,
        expected_json={
            "data": [],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 0,
                "total_pages": 0
            }
        }
    )
