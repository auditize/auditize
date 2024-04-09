import uuid

from motor.motor_asyncio import AsyncIOMotorCollection

from httpx import AsyncClient, ASGITransport, Response
from icecream import ic

from auditize.main import app
from auditize.common.mongo import mongo_client, get_db, Database

# a valid ObjectId, but not existing in the database
UNKNOWN_LOG_ID = "65fab045f097fe0b9b664c99"


def setup_test_db():
    test_db = Database("test_%s" % uuid.uuid4(), mongo_client)
    app.dependency_overrides[get_db] = lambda: test_db
    return test_db


async def teardown_test_db(test_db):
    app.dependency_overrides[get_db] = get_db
    await mongo_client.drop_database(test_db.name)


def create_http_client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost")


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected


async def assert_request(
    client: AsyncClient,
    method: str, path, *, params=None, json=None, files=None, data=None,
    expected_status_code=200, expected_json=None
) -> Response:
    ic(json, files, data)
    resp = await client.request(method, path, params=params, json=json, files=files, data=data)
    ic(resp.text)
    assert resp.status_code == expected_status_code
    if expected_json is not None:
        assert resp.json() == expected_json
    return resp


async def assert_post(
    client: AsyncClient, path, *, json=None, files=None, data=None,
    expected_status_code=200, expected_json=None
) -> Response:
    return await assert_request(
        client,
        "POST", path,
        json=json, files=files, data=data,
        expected_status_code=expected_status_code, expected_json=expected_json
    )


async def assert_patch(
    client: AsyncClient,
    path, *, json=None, files=None, data=None,
    expected_status_code=204, expected_json=None
) -> Response:
    return await assert_request(
        client,
        "PATCH", path,
        json=json, files=files, data=data,
        expected_status_code=expected_status_code, expected_json=expected_json
    )


async def assert_delete(
    client: AsyncClient,
    path, *,
    expected_status_code=204, expected_json=None
) -> Response:
    return await assert_request(
        client,
        "DELETE", path,
        expected_status_code=expected_status_code, expected_json=expected_json
    )


async def assert_get(
    client: AsyncClient,
    path, *, params=None,
    expected_status_code=200, expected_json=None
) -> Response:
    return await assert_request(
        client,
        "GET", path, params=params,
        expected_status_code=expected_status_code, expected_json=expected_json
    )


async def do_test_page_pagination_common_scenarios(client: AsyncClient, path: str, data: list):
    """
    This function assumes that for the given path (with possible query string), the total number of items is 5.
    """
    # first test, without pagination parameters
    resp = await assert_get(client, path)
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
    resp = await assert_get(client, path, params={"page": 2, "page_size": 2})
    assert resp.json() == {
        "data": data[2:4],
        "pagination": {
            "page": 2,
            "page_size": 2,
            "total": 5,
            "total_pages": 3
        }
    }


class ApiTestHelper:
    client: AsyncClient
    db: Database

    def setup_method(self):
        self.client = create_http_client()
        self.db = setup_test_db()

    async def teardown_method(self):
        # FIXME: the teardown is not awaited
        await self.client.aclose()
        await teardown_test_db(self.db)

    async def request(self, method: str, path, *, params=None, json=None, files=None, data=None,
                      expected_status_code=200):
        return await assert_request(
            self.client, method, path,
            params=params, json=json, files=files, data=data, expected_status_code=expected_status_code
        )

    async def post(self, path, *, json=None, files=None, data=None, expected_status_code=200):
        return await assert_post(
            self.client, path,
            json=json, files=files, data=data, expected_status_code=expected_status_code
        )

    async def get(self, path, *, params=None, expected_status_code=200):
        return await assert_get(
            self.client, path,
            params=params, expected_status_code=expected_status_code
        )
