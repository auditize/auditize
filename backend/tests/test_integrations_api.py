import callee
import pytest
from bson import ObjectId

from auditize.common.db import DatabaseManager
from conftest import IntegrationBuilder, UserBuilder
from helpers.database import assert_collection
from helpers.http import HttpTestHelper, create_http_client
from helpers.integrations import PreparedIntegration
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.repos import PreparedRepo

pytestmark = pytest.mark.anyio

# Make API calls as a user instead of integration to let an empty integrations collection
# when testing integrations.


async def test_integration_create(
    integration_write_client: HttpTestHelper, dbm: DatabaseManager
):
    data = PreparedIntegration.prepare_data()

    resp = await integration_write_client.assert_post(
        "/integrations",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str), "token": callee.IsA(str)},
    )

    integration = PreparedIntegration(
        resp.json()["id"], resp.json()["token"], data, dbm
    )
    await assert_collection(dbm.core_db.integrations, [integration.expected_document()])

    # Test that the token actually works
    integration_client = create_http_client()
    await integration_client.assert_get(
        "/integrations",
        headers={"Authorization": f"Bearer {integration.token}"},
        expected_status_code=403,  # 403 means that authentication was successful
    )


async def test_integration_create_custom_permissions(
    integration_write_client: HttpTestHelper, repo: PreparedRepo, dbm: DatabaseManager
):
    data = PreparedIntegration.prepare_data(
        {
            "permissions": {
                "entities": {"repos": {"read": True, "write": True}},
                "logs": {"repos": {repo.id: {"read": True, "write": True}}},
            }
        }
    )
    resp = await integration_write_client.assert_post(
        "/integrations",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str), "token": callee.IsA(str)},
    )

    integration = PreparedIntegration(
        resp.json()["id"], resp.json()["token"], data, dbm
    )
    await assert_collection(
        dbm.core_db.integrations,
        [
            integration.expected_document(
                {
                    "permissions": {
                        "is_superadmin": False,
                        "logs": {
                            "read": False,
                            "write": False,
                            "repos": {repo.id: {"read": True, "write": True}},
                        },
                        "entities": {
                            "repos": {"read": True, "write": True},
                            "users": {"read": False, "write": False},
                            "integrations": {"read": False, "write": False},
                        },
                    }
                }
            )
        ],
    )


async def test_create_integration_custom_permissions_unknown_repo(
    superadmin_client: HttpTestHelper,
):
    await superadmin_client.assert_post(
        "/integrations",
        json=PreparedIntegration.prepare_data(
            {
                "permissions": {
                    "logs": {
                        "repos": {UNKNOWN_OBJECT_ID: {"read": True, "write": True}}
                    },
                }
            }
        ),
        expected_status_code=400,
    )


async def test_integration_create_missing_parameter(
    integration_write_client: HttpTestHelper, dbm: DatabaseManager
):
    template = PreparedIntegration.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await integration_write_client.assert_post(
            "/integrations", json=data, expected_status_code=422
        )


async def test_integration_create_already_used_name(
    integration_write_client: HttpTestHelper, integration: PreparedIntegration
):
    await integration_write_client.assert_post(
        "/integrations",
        json={"name": integration.data["name"]},
        expected_status_code=409,
    )


async def test_integration_create_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_forbidden_post(
        "/integrations",
        json=PreparedIntegration.prepare_data(),
    )


async def test_integration_update(
    integration_write_client: HttpTestHelper,
    integration: PreparedIntegration,
    dbm: DatabaseManager,
):
    data = {"name": "Integration Updated"}
    await integration_write_client.assert_patch(
        f"/integrations/{integration.id}", json=data, expected_status_code=204
    )

    await assert_collection(
        dbm.core_db.integrations, [integration.expected_document(data)]
    )


async def test_user_update_permissions(
    integration_write_client: HttpTestHelper, repo: PreparedRepo, dbm: DatabaseManager
):
    integration = await PreparedIntegration.create(
        integration_write_client,
        dbm,
        PreparedIntegration.prepare_data(
            {
                "permissions": {
                    "logs": {"read": True, "write": False},
                    "entities": {
                        "repos": {"read": True, "write": True},
                    },
                }
            }
        ),
    )

    await integration_write_client.assert_patch(
        f"/integrations/{integration.id}",
        json={
            "permissions": {
                "logs": {
                    "read": False,
                    "write": False,
                    "repos": {repo.id: {"read": True, "write": True}},
                },
                "entities": {
                    "repos": {"read": False, "write": False},
                    "users": {"read": True, "write": True},
                },
            }
        },
        expected_status_code=204,
    )

    await assert_collection(
        dbm.core_db.integrations,
        [
            integration.expected_document(
                {
                    "permissions": {
                        "is_superadmin": False,
                        "logs": {
                            "read": False,
                            "write": False,
                            "repos": {repo.id: {"read": True, "write": True}},
                        },
                        "entities": {
                            "repos": {"read": False, "write": False},
                            "users": {"read": True, "write": True},
                            "integrations": {"read": False, "write": False},
                        },
                    }
                }
            )
        ],
    )


async def test_integration_update_permissions_unknown_repo(
    superadmin_client: HttpTestHelper, dbm: DatabaseManager
):
    integrations = await PreparedIntegration.create(
        superadmin_client,
        dbm,
    )

    await superadmin_client.assert_patch(
        f"/integrations/{integrations.id}",
        json={
            "permissions": {
                "logs": {
                    "repos": {UNKNOWN_OBJECT_ID: {"read": True, "write": True}},
                },
            }
        },
        expected_status_code=400,
    )


async def test_integration_update_unknown_id(integration_write_client: HttpTestHelper):
    await integration_write_client.assert_patch(
        f"/integrations/{UNKNOWN_OBJECT_ID}",
        json={"name": "update"},
        expected_status_code=404,
    )


async def test_integration_update_name_already_used(
    integration_write_client: HttpTestHelper, dbm: DatabaseManager
):
    integration1 = await PreparedIntegration.create(integration_write_client, dbm)
    integration2 = await PreparedIntegration.create(integration_write_client, dbm)

    await integration_write_client.assert_patch(
        f"/integrations/{integration1.id}",
        json={"name": integration2.data["name"]},
        expected_status_code=409,
    )


async def test_integration_update_forbidden(
    no_permission_client: HttpTestHelper, integration: PreparedIntegration
):
    await no_permission_client.assert_forbidden_patch(
        f"/integrations/{integration.id}", json={"name": "Integration Updated"}
    )


async def test_integration_update_self(integration_builder: IntegrationBuilder):
    integration = await integration_builder(
        {"entities": {"integrations": {"write": True}}}
    )
    async with integration.client() as client:
        await client.assert_forbidden_patch(
            f"/integrations/{integration.id}",
            json={"name": "Integration Updated"},
        )


async def test_integration_regenerate_token(
    integration_write_client: HttpTestHelper,
    integration: PreparedIntegration,
    dbm: DatabaseManager,
):
    mongo_document = await dbm.core_db.integrations.find_one(
        {"_id": ObjectId(integration.id)}
    )

    await integration_write_client.assert_post(
        f"/integrations/{integration.id}/token",
        expected_status_code=200,
        expected_json={"token": callee.IsA(str)},
    )

    # make sure the token has changed
    await assert_collection(
        dbm.core_db.integrations,
        [
            integration.expected_document(
                {
                    "token_hash": callee.Matching(
                        lambda val: type(val) is str
                        and val != mongo_document["token_hash"]
                    )
                }
            )
        ],
    )


async def test_integration_regenerate_token_forbidden(
    no_permission_client: HttpTestHelper, integration: PreparedIntegration
):
    await no_permission_client.assert_forbidden_post(
        f"/integrations/{integration.id}/token"
    )


async def test_integration_regenerate_token_self(integration: PreparedIntegration):
    async with integration.client() as client:
        await client.assert_forbidden_post(f"/integrations/{integration.id}/token")


async def test_integration_get(
    integration_read_client: HttpTestHelper, integration: PreparedIntegration
):
    await integration_read_client.assert_get(
        f"/integrations/{integration.id}",
        expected_status_code=200,
        expected_json=integration.expected_api_response(),
    )


async def test_integration_get_unknown_id(integration_read_client: HttpTestHelper):
    await integration_read_client.assert_get(
        f"/integrations/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_integration_get_forbidden(
    no_permission_client: HttpTestHelper, integration: PreparedIntegration
):
    await no_permission_client.assert_forbidden_get(f"/integrations/{integration.id}")


async def test_integration_list(
    integration_read_client: HttpTestHelper,
    integration_write_client: HttpTestHelper,
    dbm: DatabaseManager,
):
    integrations = [
        await PreparedIntegration.create(integration_write_client, dbm)
        for _ in range(5)
    ]

    await do_test_page_pagination_common_scenarios(
        integration_read_client,
        "/integrations",
        [
            integration.expected_api_response()
            for integration in sorted(integrations, key=lambda r: r.data["name"])
        ],
    )


async def test_integration_list_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_forbidden_get("/integrations")


async def test_integration_delete(
    integration_write_client: HttpTestHelper,
    integration: PreparedIntegration,
    dbm: DatabaseManager,
):
    await integration_write_client.assert_delete(
        f"/integrations/{integration.id}", expected_status_code=204
    )

    await assert_collection(dbm.core_db.integrations, [])


async def test_integration_delete_unknown_id(integration_write_client: HttpTestHelper):
    await integration_write_client.assert_delete(
        f"/integrations/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_integration_delete_unauthorized(
    no_permission_client: HttpTestHelper, integration: PreparedIntegration
):
    await no_permission_client.assert_forbidden_delete(
        f"/integrations/{integration.id}"
    )


async def test_integration_delete_self(integration: PreparedIntegration):
    async with integration.client() as client:
        await client.assert_forbidden_delete(f"/integrations/{integration.id}")
