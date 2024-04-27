from bson import ObjectId

import pytest
import callee

from auditize.common.db import DatabaseManager

from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.database import assert_collection
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.http import HttpTestHelper, create_http_client
from helpers.integrations import PreparedIntegration

pytestmark = pytest.mark.anyio

# Use user_client instead of integration_client to let an empty integrations collection
# when testing integrations.


async def test_integration_create(user_client: HttpTestHelper, dbm: DatabaseManager):
    data = PreparedIntegration.prepare_data()

    resp = await user_client.assert_post(
        "/integrations", json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str), "token": callee.IsA(str)}
    )

    integration = PreparedIntegration(resp.json()["id"], resp.json()["token"], data, dbm)
    await assert_collection(dbm.core_db.integrations, [integration.expected_document()])

    # Test that the token actually works
    integration_client = create_http_client()
    await integration_client.assert_get(
        "/integrations",
        headers={
            "Authorization": f"Bearer {integration.token}"
        },
        expected_status_code=200
    )


async def test_integration_create_missing_parameter(user_client: HttpTestHelper, dbm: DatabaseManager):
    template = PreparedIntegration.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await user_client.assert_post(
            "/integrations", json=data,
            expected_status_code=422
        )


async def test_integration_create_already_used_name(user_client: HttpTestHelper, integration: PreparedIntegration):
    await user_client.assert_post(
        "/integrations", json={
            "name": integration.data["name"]
        },
        expected_status_code=409
    )


async def test_integration_update(user_client: HttpTestHelper, integration: PreparedIntegration, dbm: DatabaseManager):
    data = {"name": "Integration Updated"}
    await user_client.assert_patch(
        f"/integrations/{integration.id}", json=data,
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.integrations, [integration.expected_document(data)])


async def test_integration_regenerate_token(user_client: HttpTestHelper, integration: PreparedIntegration, dbm: DatabaseManager):
    mongo_document = await dbm.core_db.integrations.find_one({"_id": ObjectId(integration.id)})

    await user_client.assert_post(
        f"/integrations/{integration.id}/token",
        expected_status_code=200,
        expected_json={"token": callee.IsA(str)}
    )

    # make sure the token has changed
    await assert_collection(dbm.core_db.integrations, [integration.expected_document({
        "token_hash": callee.Matching(lambda val: type(val) is str and val != mongo_document["token_hash"])
    })])


async def test_integration_update_unknown_id(user_client: HttpTestHelper):
    await user_client.assert_patch(
        f"/integrations/{UNKNOWN_OBJECT_ID}", json={"name": "update"},
        expected_status_code=404
    )


async def test_integration_update_already_name(user_client: HttpTestHelper, dbm: DatabaseManager):
    integration1 = await PreparedIntegration.create(user_client, dbm)
    integration2 = await PreparedIntegration.create(user_client, dbm)

    await user_client.assert_patch(
        f"/integrations/{integration1.id}", json={"name": integration2.data["name"]},
        expected_status_code=409
    )


async def test_integration_get(user_client: HttpTestHelper, integration: PreparedIntegration):
    await user_client.assert_get(
        f"/integrations/{integration.id}",
        expected_status_code=200,
        expected_json=integration.expected_api_response()
    )


async def test_integration_get_unknown_id(user_client: HttpTestHelper):
    await user_client.assert_get(
        f"/integrations/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )


async def test_integration_list(user_client: HttpTestHelper, dbm: DatabaseManager):
    integrations = [await PreparedIntegration.create(user_client, dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        user_client, "/integrations",
        [integration.expected_api_response() for integration in sorted(integrations, key=lambda r: r.data["name"])]
    )


async def test_integration_delete(user_client: HttpTestHelper, integration: PreparedIntegration, dbm: DatabaseManager):
    await user_client.assert_delete(
        f"/integrations/{integration.id}",
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.integrations, [])


async def test_integration_delete_unknown_id(user_client: HttpTestHelper):
    await user_client.assert_delete(
        f"/integrations/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )
