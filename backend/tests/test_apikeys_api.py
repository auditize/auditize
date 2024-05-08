import callee
import pytest
from bson import ObjectId
from httpx import Response

from auditize.database import DatabaseManager
from conftest import ApikeyBuilder
from helpers.apikeys import PreparedApikey
from helpers.database import assert_collection
from helpers.http import HttpTestHelper, create_http_client
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.permissions.tests import BasePermissionTests
from helpers.users import PreparedUser

pytestmark = pytest.mark.anyio


# Make API calls as a user instead of apikey to let an empty apikeys collection
# when testing apikeys.


async def test_apikey_create(apikey_write_client: HttpTestHelper, dbm: DatabaseManager):
    data = PreparedApikey.prepare_data()

    resp = await apikey_write_client.assert_post(
        "/apikeys",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str), "token": callee.IsA(str)},
    )

    apikey = PreparedApikey(resp.json()["id"], resp.json()["token"], data, dbm)
    await assert_collection(dbm.core_db.apikeys, [apikey.expected_document()])

    # Test that the token actually works
    apikey_client = create_http_client()
    await apikey_client.assert_get(
        "/apikeys",
        headers={"Authorization": f"Bearer {apikey.token}"},
        expected_status_code=403,  # 403 means that authentication was successful, otherwise it would be 401
    )


async def test_apikey_create_missing_parameter(
    apikey_write_client: HttpTestHelper, dbm: DatabaseManager
):
    template = PreparedApikey.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await apikey_write_client.assert_post(
            "/apikeys", json=data, expected_status_code=422
        )


async def test_apikey_create_already_used_name(
    apikey_write_client: HttpTestHelper, apikey: PreparedApikey
):
    await apikey_write_client.assert_post(
        "/apikeys",
        json={"name": apikey.data["name"]},
        expected_status_code=409,
    )


async def test_apikey_create_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_forbidden_post(
        "/apikeys",
        json=PreparedApikey.prepare_data(),
    )


async def test_apikey_update(
    apikey_write_client: HttpTestHelper,
    apikey: PreparedApikey,
    dbm: DatabaseManager,
):
    data = {"name": "Apikey Updated"}
    await apikey_write_client.assert_patch(
        f"/apikeys/{apikey.id}", json=data, expected_status_code=204
    )

    await assert_collection(dbm.core_db.apikeys, [apikey.expected_document(data)])


async def test_apikey_update_unknown_id(apikey_write_client: HttpTestHelper):
    await apikey_write_client.assert_patch(
        f"/apikeys/{UNKNOWN_OBJECT_ID}",
        json={"name": "update"},
        expected_status_code=404,
    )


async def test_apikey_update_name_already_used(
    apikey_write_client: HttpTestHelper, dbm: DatabaseManager
):
    apikey1 = await PreparedApikey.create(apikey_write_client, dbm)
    apikey2 = await PreparedApikey.create(apikey_write_client, dbm)

    await apikey_write_client.assert_patch(
        f"/apikeys/{apikey1.id}",
        json={"name": apikey2.data["name"]},
        expected_status_code=409,
    )


async def test_apikey_update_forbidden(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_forbidden_patch(
        f"/apikeys/{apikey.id}", json={"name": "Apikey Updated"}
    )


async def test_apikey_update_self(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({"management": {"apikeys": {"write": True}}})
    async with apikey.client() as client:
        await client.assert_forbidden_patch(
            f"/apikeys/{apikey.id}",
            json={"name": "Apikey Updated"},
        )


async def test_apikey_regenerate_token(
    apikey_write_client: HttpTestHelper,
    apikey: PreparedApikey,
    dbm: DatabaseManager,
):
    mongo_document = await dbm.core_db.apikeys.find_one({"_id": ObjectId(apikey.id)})

    await apikey_write_client.assert_post(
        f"/apikeys/{apikey.id}/token",
        expected_status_code=200,
        expected_json={"token": callee.IsA(str)},
    )

    # make sure the token has changed
    await assert_collection(
        dbm.core_db.apikeys,
        [
            apikey.expected_document(
                {
                    "token_hash": callee.Matching(
                        lambda val: type(val) is str
                        and val != mongo_document["token_hash"]
                    )
                }
            )
        ],
    )


async def test_apikey_regenerate_token_forbidden(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_forbidden_post(f"/apikeys/{apikey.id}/token")


async def test_apikey_regenerate_token_self(apikey: PreparedApikey):
    async with apikey.client() as client:
        await client.assert_forbidden_post(f"/apikeys/{apikey.id}/token")


async def test_apikey_get(apikey_read_client: HttpTestHelper, apikey: PreparedApikey):
    await apikey_read_client.assert_get(
        f"/apikeys/{apikey.id}",
        expected_status_code=200,
        expected_json=apikey.expected_api_response(),
    )


async def test_apikey_get_unknown_id(apikey_read_client: HttpTestHelper):
    await apikey_read_client.assert_get(
        f"/apikeys/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_apikey_get_forbidden(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_forbidden_get(f"/apikeys/{apikey.id}")


async def test_apikey_list(
    apikey_read_client: HttpTestHelper,
    apikey_write_client: HttpTestHelper,
    dbm: DatabaseManager,
):
    apikeys = [await PreparedApikey.create(apikey_write_client, dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        apikey_read_client,
        "/apikeys",
        [
            apikey.expected_api_response()
            for apikey in sorted(apikeys, key=lambda r: r.data["name"])
        ],
    )


async def test_apikey_list_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_forbidden_get("/apikeys")


async def test_apikey_delete(
    apikey_write_client: HttpTestHelper,
    apikey: PreparedApikey,
    dbm: DatabaseManager,
):
    await apikey_write_client.assert_delete(
        f"/apikeys/{apikey.id}", expected_status_code=204
    )

    await assert_collection(dbm.core_db.apikeys, [])


async def test_apikey_delete_unknown_id(apikey_write_client: HttpTestHelper):
    await apikey_write_client.assert_delete(
        f"/apikeys/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_apikey_delete_unauthorized(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_forbidden_delete(f"/apikeys/{apikey.id}")


async def test_apikey_delete_self(apikey: PreparedApikey):
    async with apikey.client() as client:
        await client.assert_forbidden_delete(f"/apikeys/{apikey.id}")


class TestPermissions(BasePermissionTests):
    @property
    def base_path(self):
        return "/apikeys"

    def get_principal_collection(self, dbm: DatabaseManager):
        return dbm.core_db.apikeys

    async def inject_grantor(
        self, dbm: DatabaseManager, permissions=None
    ) -> PreparedUser:
        return await PreparedUser.inject_into_db(
            dbm,
            user=PreparedUser.prepare_model(password="dummy", permissions=permissions),
            password="dummy",
        )

    def prepare_assignee_data(self, permissions=None):
        return PreparedApikey.prepare_data(permissions)

    async def create_assignee(
        self, client: HttpTestHelper, dbm: DatabaseManager, data=None
    ) -> PreparedApikey:
        return await PreparedApikey.create(client, dbm, data)

    def rebuild_assignee_from_response(
        self, resp: Response, data: dict, dbm: DatabaseManager
    ) -> PreparedApikey:
        return PreparedApikey(resp.json()["id"], resp.json()["token"], data, dbm)
