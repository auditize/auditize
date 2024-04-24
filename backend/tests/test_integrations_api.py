from bson import ObjectId

import pytest
import callee

from auditize.common.db import DatabaseManager

from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.database import assert_collection
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.http import HttpTestHelper
from helpers.integrations import PreparedIntegration

pytestmark = pytest.mark.anyio


async def test_integration_create(client: HttpTestHelper, dbm: DatabaseManager):
    data = PreparedIntegration.prepare_data()

    resp = await client.assert_post(
        "/integrations", json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str), "token": callee.IsA(str)}
    )

    integration = PreparedIntegration(resp.json()["id"], resp.json()["token"], data, dbm)
    await assert_collection(dbm.core_db.integrations, [integration.expected_document()])


async def test_integration_create_missing_parameter(client: HttpTestHelper, dbm: DatabaseManager):
    template = PreparedIntegration.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await client.assert_post(
            "/integrations", json=data,
            expected_status_code=422
        )


async def test_integration_create_already_used_name(client: HttpTestHelper, integration: PreparedIntegration):
    await client.assert_post(
        "/integrations", json={
            "name": integration.data["name"]
        },
        expected_status_code=409
    )


async def test_integration_update(client: HttpTestHelper, integration: PreparedIntegration, dbm: DatabaseManager):
    data = {"name": "Integration Updated"}
    await client.assert_patch(
        f"/integrations/{integration.id}", json=data,
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.integrations, [integration.expected_document(data)])


async def test_integration_regenerate_token(client: HttpTestHelper, integration: PreparedIntegration, dbm: DatabaseManager):
    mongo_document = await dbm.core_db.integrations.find_one({"_id": ObjectId(integration.id)})

    await client.assert_post(
        f"/integrations/{integration.id}/token",
        expected_status_code=200,
        expected_json={"token": callee.IsA(str)}
    )

    # make sure the token has changed
    await assert_collection(dbm.core_db.integrations, [integration.expected_document({
        "token_hash": callee.Matching(lambda val: type(val) is str and val != mongo_document["token_hash"])
    })])


async def test_integration_update_unknown_id(client: HttpTestHelper):
    await client.assert_patch(
        f"/integrations/{UNKNOWN_OBJECT_ID}", json={"name": "update"},
        expected_status_code=404
    )


async def test_integration_update_already_name(client: HttpTestHelper, dbm: DatabaseManager):
    integration1 = await PreparedIntegration.create(client, dbm)
    integration2 = await PreparedIntegration.create(client, dbm)

    await client.assert_patch(
        f"/integrations/{integration1.id}", json={"name": integration2.data["name"]},
        expected_status_code=409
    )


async def test_integration_get(client: HttpTestHelper, integration: PreparedIntegration):
    await client.assert_get(
        f"/integrations/{integration.id}",
        expected_status_code=200,
        expected_json=integration.expected_api_response()
    )


async def test_integration_get_unknown_id(client: HttpTestHelper):
    await client.assert_get(
        f"/integrations/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )


async def test_integration_list(client: HttpTestHelper, dbm: DatabaseManager):
    integrations = [await PreparedIntegration.create(client, dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        client, "/integrations",
        [integration.expected_api_response() for integration in sorted(integrations, key=lambda r: r.data["name"])]
    )


async def test_integration_delete(client: HttpTestHelper, integration: PreparedIntegration, dbm: DatabaseManager):
    await client.assert_delete(
        f"/integrations/{integration.id}",
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.integrations, [])


async def test_integration_delete_unknown_id(client: HttpTestHelper):
    await client.assert_delete(
        f"/integrations/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )
