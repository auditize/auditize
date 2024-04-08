from motor.motor_asyncio import AsyncIOMotorCollection

from httpx import AsyncClient, Response
from icecream import ic


async def assert_collection(collection: AsyncIOMotorCollection, expected):
    results = await collection.find({}).to_list(None)
    assert results == expected


async def assert_request(method: str, client: AsyncClient, path, *, params=None, json=None, files=None, data=None,
                         expected_status_code=200) -> Response:
    ic(json, files, data)
    resp = await client.request(method, path, params=params, json=json, files=files, data=data)
    ic(resp.text)
    assert resp.status_code == expected_status_code
    return resp


async def assert_post(client: AsyncClient, path, *, json=None, files=None, data=None, expected_status_code=200) -> Response:
    return await assert_request(
        "POST", client, path,
        json=json, files=files, data=data, expected_status_code=expected_status_code
    )


async def assert_get(client: AsyncClient, path, *, params=None, expected_status_code=200) -> Response:
    return await assert_request("GET", client, path, params=params, expected_status_code=expected_status_code)
