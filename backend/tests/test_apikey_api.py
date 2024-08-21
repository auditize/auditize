import uuid

import callee
import pytest
from httpx import Response

from auditize.database import DatabaseManager
from conftest import ApikeyBuilder
from helpers.apikey import PreparedApikey
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.log import UNKNOWN_UUID
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.permissions.tests import BasePermissionTests
from helpers.user import PreparedUser

pytestmark = pytest.mark.anyio


# Make API calls as a user instead of apikey to let an empty apikeys collection
# when testing apikeys.


async def test_apikey_create(apikey_write_client: HttpTestHelper, dbm: DatabaseManager):
    data = PreparedApikey.prepare_data()

    resp = await apikey_write_client.assert_post(
        "/apikeys",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str), "key": callee.IsA(str)},
    )

    apikey = PreparedApikey(resp.json()["id"], resp.json()["key"], data)
    await assert_collection(dbm.core_db.apikeys, [apikey.expected_document()])

    # Test that the key actually works
    apikey_client = HttpTestHelper.spawn()
    await apikey_client.assert_get(
        "/apikeys",
        headers={"Authorization": f"Bearer {apikey.key}"},
        expected_status_code=403,  # 403 means that authentication was successful, otherwise it would be 401
    )


async def test_apikey_create_missing_parameter(
    apikey_write_client: HttpTestHelper, dbm: DatabaseManager
):
    template = PreparedApikey.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await apikey_write_client.assert_post_bad_request(
            "/apikeys",
            json=data,
            expected_json={
                "message": "Invalid request",
                "localized_message": None,
                "validation_errors": [
                    {
                        "field": key,
                        "message": "Field required",
                    }
                ],
            },
        )


async def test_apikey_create_already_used_name(
    apikey_write_client: HttpTestHelper, apikey: PreparedApikey
):
    await apikey_write_client.assert_post_constraint_violation(
        "/apikeys",
        json={"name": apikey.data["name"]},
    )


async def test_apikey_create_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_post_forbidden(
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
    await apikey_write_client.assert_patch_not_found(
        f"/apikeys/{UNKNOWN_UUID}",
        json={"name": "update"},
    )


async def test_apikey_update_name_already_used(
    apikey_write_client: HttpTestHelper, dbm: DatabaseManager
):
    apikey1 = await PreparedApikey.create(apikey_write_client)
    apikey2 = await PreparedApikey.create(apikey_write_client)

    await apikey_write_client.assert_patch_constraint_violation(
        f"/apikeys/{apikey1.id}",
        json={"name": apikey2.data["name"]},
    )


async def test_apikey_update_forbidden(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_patch_forbidden(
        f"/apikeys/{apikey.id}", json={"name": "Apikey Updated"}
    )


async def test_apikey_update_self(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({"management": {"apikeys": {"write": True}}})
    async with apikey.client() as client:
        await client.assert_patch_forbidden(
            f"/apikeys/{apikey.id}",
            json={"name": "Apikey Updated"},
        )


async def test_apikey_regenerate_key(
    apikey_write_client: HttpTestHelper,
    apikey: PreparedApikey,
    dbm: DatabaseManager,
):
    mongo_document = await dbm.core_db.apikeys.find_one({"_id": uuid.UUID(apikey.id)})

    await apikey_write_client.assert_post(
        f"/apikeys/{apikey.id}/key",
        expected_status_code=200,
        expected_json={"key": callee.IsA(str)},
    )

    # make sure the key has changed
    await assert_collection(
        dbm.core_db.apikeys,
        [
            apikey.expected_document(
                {
                    "key_hash": callee.Matching(
                        lambda val: (
                            type(val) is str and val != mongo_document["key_hash"]
                        )
                    )
                }
            )
        ],
    )


async def test_apikey_regenerate_key_forbidden(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_post_forbidden(f"/apikeys/{apikey.id}/key")


async def test_apikey_regenerate_key_self(apikey: PreparedApikey):
    async with apikey.client() as client:
        await client.assert_post_forbidden(f"/apikeys/{apikey.id}/key")


async def test_apikey_get(apikey_read_client: HttpTestHelper, apikey: PreparedApikey):
    await apikey_read_client.assert_get(
        f"/apikeys/{apikey.id}",
        expected_status_code=200,
        expected_json=apikey.expected_api_response(),
    )


async def test_apikey_get_unknown_id(apikey_read_client: HttpTestHelper):
    await apikey_read_client.assert_get_not_found(f"/apikeys/{UNKNOWN_UUID}")


async def test_apikey_get_forbidden(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_get_forbidden(f"/apikeys/{apikey.id}")


async def test_apikey_list(
    apikey_read_client: HttpTestHelper,
    apikey_write_client: HttpTestHelper,
    dbm: DatabaseManager,
):
    apikeys = [await PreparedApikey.create(apikey_write_client) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        apikey_read_client,
        "/apikeys",
        [
            apikey.expected_api_response()
            for apikey in sorted(apikeys, key=lambda ak: ak.data["name"])
        ],
    )


async def test_apikey_list_search(
    apikey_rw_client: HttpTestHelper,
    dbm: DatabaseManager,
):
    apikeys = [
        await PreparedApikey.create(apikey_rw_client, {"name": f"apikey_{i}"})
        for i in range(2)
    ]

    await apikey_rw_client.assert_get_ok(
        "/apikeys?q=apikey_1",
        expected_json={
            "items": [apikeys[1].expected_api_response()],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_apikey_list_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_get_forbidden("/apikeys")


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
    await apikey_write_client.assert_delete_not_found(f"/apikeys/{UNKNOWN_UUID}")


async def test_apikey_delete_unauthorized(
    no_permission_client: HttpTestHelper, apikey: PreparedApikey
):
    await no_permission_client.assert_delete_forbidden(f"/apikeys/{apikey.id}")


async def test_apikey_delete_self(apikey: PreparedApikey):
    async with apikey.client() as client:
        await client.assert_delete_forbidden(f"/apikeys/{apikey.id}")


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
            user=PreparedUser.prepare_model(
                password="dummypassword", permissions=permissions
            ),
            password="dummypassword",
        )

    def prepare_assignee_data(self, permissions=None):
        return PreparedApikey.prepare_data(permissions)

    async def create_assignee(
        self, client: HttpTestHelper, dbm: DatabaseManager, data=None
    ) -> PreparedApikey:
        return await PreparedApikey.create(client, data)

    def rebuild_assignee_from_response(
        self, resp: Response, data: dict, dbm: DatabaseManager
    ) -> PreparedApikey:
        return PreparedApikey(resp.json()["id"], resp.json()["key"], data)
