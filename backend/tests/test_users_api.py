from unittest.mock import patch

import pytest
import callee

from auditize.common.db import DatabaseManager

from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.database import assert_collection
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.http import HttpTestHelper
from helpers.users import PreparedUser

pytestmark = pytest.mark.anyio

UNKNOWN_SIGNUP_TOKEN = "5620281609bbdc9796751a1cb1ac58efb27497b1fd14a0788faa83ada93e6048"


async def test_user_create(client: HttpTestHelper, dbm: DatabaseManager):
    data = PreparedUser.prepare_data()

    with patch("auditize.users.service.send_email") as mock:
        resp = await client.assert_post(
            "/users", json=data,
            expected_status_code=201,
            expected_json={"id": callee.IsA(str)}
        )
        mock.assert_called_once_with(
            data["email"],  # to
            callee.IsA(str),  # subject
            callee.Regex(".*/signup/[0-9a-f]{64}.*")  # body
        )

    user = PreparedUser(resp.json()["id"], data, dbm)
    await assert_collection(dbm.core_db.users, [user.expected_document()])


async def test_user_create_missing_parameter(client: HttpTestHelper, dbm: DatabaseManager):
    template = PreparedUser.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await client.assert_post(
            "/users", json=data,
            expected_status_code=422
        )


async def test_user_create_already_used_email(client: HttpTestHelper, user: PreparedUser):
    await client.assert_post(
        "/users", json={
            "email": user.data["email"], "first_name": "Another John", "last_name": "Another Doe"
        },
        expected_status_code=409
    )


async def test_user_update_all(client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager):
    data = {
        "first_name": "John Updated", "last_name": "Doe Updated", "email": "john.doe_updated@example.net"
    }
    await client.assert_patch(
        f"/users/{user.id}", json=data,
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.users, [user.expected_document(data)])


async def test_user_update_partial(client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager):
    data = {"first_name": "John Updated"}
    await client.assert_patch(
        f"/users/{user.id}", json=data,
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.users, [user.expected_document(data)])


async def test_user_update_unknown_id(client: HttpTestHelper):
    await client.assert_patch(
        f"/users/{UNKNOWN_OBJECT_ID}", json={"first_name": "John Updated"},
        expected_status_code=404
    )


async def test_user_update_already_used_email(client: HttpTestHelper, dbm: DatabaseManager):
    user1 = await PreparedUser.create(client, dbm)
    user2 = await PreparedUser.create(client, dbm)

    await client.assert_patch(
        f"/users/{user1.id}", json={"email": user2.data["email"]},
        expected_status_code=409
    )


async def test_user_get(client: HttpTestHelper, user: PreparedUser):
    await client.assert_get(
        f"/users/{user.id}",
        expected_status_code=200,
        expected_json=user.expected_api_response()
    )


async def test_user_get_unknown_id(client: HttpTestHelper):
    await client.assert_get(
        f"/users/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )


async def test_user_list(client: HttpTestHelper, dbm: DatabaseManager):
    users = [await PreparedUser.create(client, dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        client, "/users",
        [user.expected_api_response() for user in sorted(users, key=lambda r: r.data["last_name"])]
    )


async def test_user_delete(client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager):
    await client.assert_delete(
        f"/users/{user.id}",
        expected_status_code=204
    )

    await assert_collection(dbm.core_db.users, [])


async def test_user_delete_unknown_id(client: HttpTestHelper):
    await client.assert_delete(
        f"/users/{UNKNOWN_OBJECT_ID}",
        expected_status_code=404
    )


async def test_user_signup(client: HttpTestHelper, user: PreparedUser):
    await client.assert_get(
        f"/users/signup/{await user.signup_token}",
        expected_status_code=200,
        expected_json={
            "first_name": user.data["first_name"],
            "last_name": user.data["last_name"],
            "email": user.data["email"]
        }
    )


async def test_user_signup_expired(client: HttpTestHelper, user: PreparedUser):
    await user.expire_signup_token()
    await client.assert_get(
        f"/users/signup/{await user.signup_token}",
        expected_status_code=404,
    )


async def test_user_signup_unknown(client: HttpTestHelper):
    await client.assert_get(
        f"/users/signup/{UNKNOWN_SIGNUP_TOKEN}",
        expected_status_code=404,
    )


async def test_user_signup_set_password(client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager):
    await client.assert_post(
        f"/users/signup/{await user.signup_token}", json={"password": "new_password"},
        expected_status_code=204
    )

    await assert_collection(
        dbm.core_db.users, [user.expected_document({
            "password_hash": callee.IsA(str),
            "signup_token": None
        })]
    )


async def test_user_signup_set_password_token_expired(client: HttpTestHelper, user: PreparedUser):
    await user.expire_signup_token()
    await client.assert_post(
        f"/users/signup/{await user.signup_token}", json={"password": "new_password"},
        expected_status_code=404
    )


async def test_user_signup_set_password_token_unknown(client: HttpTestHelper):
    await client.assert_post(
        f"/users/signup/{UNKNOWN_SIGNUP_TOKEN}", json={"password": "new_password"},
        expected_status_code=404
    )
