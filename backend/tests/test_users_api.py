import time
from unittest.mock import patch

import callee
import pytest
from icecream import ic
from tests.conftest import UserBuilder

from auditize.common.db import DatabaseManager
from helpers.database import assert_collection
from helpers.http import HttpTestHelper, get_cookie_by_name
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.permissions import DEFAULT_APPLICABLE_PERMISSIONS
from helpers.users import PreparedUser

pytestmark = pytest.mark.anyio

UNKNOWN_SIGNUP_TOKEN = (
    "5620281609bbdc9796751a1cb1ac58efb27497b1fd14a0788faa83ada93e6048"
)


async def test_user_create(user_write_client: HttpTestHelper, dbm: DatabaseManager):
    data = PreparedUser.prepare_data()

    with patch("auditize.users.service.send_email") as mock:
        resp = await user_write_client.assert_post(
            "/users",
            json=data,
            expected_status_code=201,
            expected_json={"id": callee.IsA(str)},
        )
        mock.assert_called_once_with(
            data["email"],  # to
            callee.IsA(str),  # subject
            callee.Regex(".*/signup/[0-9a-f]{64}.*"),  # body
        )

    user = PreparedUser(resp.json()["id"], data, dbm)
    await assert_collection(dbm.core_db.users, [user.expected_document()])


async def test_user_create_custom_permissions(
    superadmin_client: HttpTestHelper, dbm: DatabaseManager
):
    data = PreparedUser.prepare_data(
        extra={"permissions": {"logs": {"read": True, "write": True}}}
    )
    resp = await superadmin_client.assert_post(
        "/users",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)},
    )

    user = PreparedUser(resp.json()["id"], data, dbm)
    await assert_collection(
        dbm.core_db.users,
        [
            user.expected_document(
                {
                    "permissions": {
                        "is_superadmin": False,
                        "logs": {"read": True, "write": True, "repos": {}},
                        "entities": {
                            "repos": {"read": False, "write": False},
                            "users": {"read": False, "write": False},
                            "integrations": {"read": False, "write": False},
                        },
                    }
                }
            )
        ],
    )


async def test_user_create_missing_parameter(
    user_write_client: HttpTestHelper, dbm: DatabaseManager
):
    template = PreparedUser.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await user_write_client.assert_post(
            "/users", json=data, expected_status_code=422
        )


async def test_user_create_already_used_email(
    user_write_client: HttpTestHelper, user: PreparedUser
):
    await user_write_client.assert_post(
        "/users",
        json={
            "email": user.data["email"],
            "first_name": "Another John",
            "last_name": "Another Doe",
        },
        expected_status_code=409,
    )


async def test_user_create_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_forbidden_post(
        "/users", json=PreparedUser.prepare_data()
    )


async def test_user_update_multiple(
    user_write_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    data = {
        "first_name": "John Updated",
        "last_name": "Doe Updated",
        "email": "john.doe_updated@example.net",
    }
    await user_write_client.assert_patch(
        f"/users/{user.id}", json=data, expected_status_code=204
    )

    await assert_collection(dbm.core_db.users, [user.expected_document(data)])


async def test_user_update_partial(
    user_write_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    data = {"first_name": "John Updated"}
    await user_write_client.assert_patch(
        f"/users/{user.id}", json=data, expected_status_code=204
    )

    await assert_collection(dbm.core_db.users, [user.expected_document(data)])


async def test_user_update_permissions(
    superadmin_client: HttpTestHelper, dbm: DatabaseManager
):
    user = await PreparedUser.create(
        superadmin_client,
        dbm,
        PreparedUser.prepare_data(
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

    await superadmin_client.assert_patch(
        f"/users/{user.id}",
        json={
            "permissions": {
                "logs": {"write": True},
                "entities": {
                    "repos": {"read": False, "write": False},
                    "users": {"read": True, "write": True},
                },
            }
        },
        expected_status_code=204,
    )

    await assert_collection(
        dbm.core_db.users,
        [
            user.expected_document(
                {
                    "permissions": {
                        "is_superadmin": False,
                        "logs": {"read": True, "write": True, "repos": {}},
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


async def test_user_update_unknown_id(user_write_client: HttpTestHelper):
    await user_write_client.assert_patch(
        f"/users/{UNKNOWN_OBJECT_ID}",
        json={"first_name": "John Updated"},
        expected_status_code=404,
    )


async def test_user_update_already_used_email(
    user_write_client: HttpTestHelper, dbm: DatabaseManager
):
    user1 = await PreparedUser.create(user_write_client, dbm)
    user2 = await PreparedUser.create(user_write_client, dbm)

    await user_write_client.assert_patch(
        f"/users/{user1.id}",
        json={"email": user2.data["email"]},
        expected_status_code=409,
    )


async def test_user_update_forbidden(
    no_permission_client: HttpTestHelper, user: PreparedUser
):
    await no_permission_client.assert_forbidden_patch(
        f"/users/{user.id}", json={"first_name": "John Updated"}
    )


async def test_user_update_self(user_builder: UserBuilder):
    user = await user_builder(
        {
            "entities": {
                "users": {"read": True, "write": True},
            }
        }
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_forbidden_patch(
            f"/users/{user.id}", json={"first_name": "John Updated"}
        )


async def test_user_get(user_read_client: HttpTestHelper, user: PreparedUser):
    await user_read_client.assert_get(
        f"/users/{user.id}",
        expected_status_code=200,
        expected_json=user.expected_api_response(),
    )


async def test_user_get_unknown_id(user_read_client: HttpTestHelper):
    await user_read_client.assert_get(
        f"/users/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_user_get_forbidden(
    no_permission_client: HttpTestHelper, user: PreparedUser
):
    await no_permission_client.assert_forbidden_get(f"/users/{user.id}")


async def test_user_list(
    user_read_client: HttpTestHelper,
    user_write_client: HttpTestHelper,
    dbm: DatabaseManager,
):
    users = [await PreparedUser.create(user_write_client, dbm) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        user_read_client,
        "/users",
        [
            user.expected_api_response()
            for user in sorted(users, key=lambda r: r.data["last_name"])
        ],
    )


async def test_user_list_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_forbidden_get("/users")


async def test_user_delete(
    user_write_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    await user_write_client.assert_delete(f"/users/{user.id}", expected_status_code=204)

    await assert_collection(dbm.core_db.users, [])


async def test_user_delete_unknown_id(user_write_client: HttpTestHelper):
    await user_write_client.assert_delete(
        f"/users/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_user_delete_forbidden(
    no_permission_client: HttpTestHelper, user: PreparedUser
):
    await no_permission_client.assert_forbidden_delete(f"/users/{user.id}")


async def test_user_delete_self(user_builder: UserBuilder):
    user = await user_builder(
        {
            "entities": {
                "users": {"read": True, "write": True},
            }
        }
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_forbidden_delete(f"/users/{user.id}")


async def test_user_signup(anon_client: HttpTestHelper, user: PreparedUser):
    await anon_client.assert_get(
        f"/users/signup/{await user.signup_token}",
        expected_status_code=200,
        expected_json={
            "first_name": user.data["first_name"],
            "last_name": user.data["last_name"],
            "email": user.data["email"],
        },
    )


async def test_user_signup_expired(anon_client: HttpTestHelper, user: PreparedUser):
    await user.expire_signup_token()
    await anon_client.assert_get(
        f"/users/signup/{await user.signup_token}",
        expected_status_code=404,
    )


async def test_user_signup_unknown(anon_client: HttpTestHelper):
    await anon_client.assert_get(
        f"/users/signup/{UNKNOWN_SIGNUP_TOKEN}",
        expected_status_code=404,
    )


async def test_user_signup_set_password(
    anon_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    await anon_client.assert_post(
        f"/users/signup/{await user.signup_token}",
        json={"password": "new_password"},
        expected_status_code=204,
    )

    await assert_collection(
        dbm.core_db.users,
        [
            user.expected_document(
                {"password_hash": callee.IsA(str), "signup_token": None}
            )
        ],
    )


async def test_user_signup_set_password_token_expired(
    anon_client: HttpTestHelper, user: PreparedUser
):
    await user.expire_signup_token()
    await anon_client.assert_post(
        f"/users/signup/{await user.signup_token}",
        json={"password": "new_password"},
        expected_status_code=404,
    )


async def test_user_signup_set_password_token_unknown(anon_client: HttpTestHelper):
    await anon_client.assert_post(
        f"/users/signup/{UNKNOWN_SIGNUP_TOKEN}",
        json={"password": "new_password"},
        expected_status_code=404,
    )


async def test_user_log_in(anon_client: HttpTestHelper, dbm: DatabaseManager):
    user = await PreparedUser.inject_into_db(dbm)
    now = int(time.time())
    resp = await anon_client.assert_post(
        "/users/login",
        json={"email": user.email, "password": user.password},
        expected_status_code=204,
    )
    ic(resp.cookies)
    cookie = get_cookie_by_name(resp, "session")
    assert cookie.name == "session"
    assert cookie.expires > now
    assert cookie.path == "/"
    assert cookie.secure is True
    assert cookie.value
    assert cookie.has_nonstandard_attr("HttpOnly")
    assert cookie.get_nonstandard_attr("SameSite") == "strict"

    # test that the cookie auth actually works
    await anon_client.assert_get("/users/me", expected_status_code=200)


async def test_get_user_me(dbm: DatabaseManager):
    user = await PreparedUser.inject_into_db(dbm)
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get(
            "/users/me",
            expected_status_code=200,
            expected_json={
                "id": user.id,
                "first_name": user.data["first_name"],
                "last_name": user.data["last_name"],
                "email": user.data["email"],
                "permissions": DEFAULT_APPLICABLE_PERMISSIONS,
            },
        )


async def test_get_user_me_unauthorized(anon_client: HttpTestHelper):
    await anon_client.assert_unauthorized_get("/users/me")


async def test_get_user_me_as_integration(integration_client: HttpTestHelper):
    await integration_client.assert_unauthorized_get("/users/me")
