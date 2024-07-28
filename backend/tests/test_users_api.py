import re
from unittest.mock import patch

import callee
import pytest
from bson import ObjectId
from httpx import Response

from auditize.database import DatabaseManager
from auditize.users.api import get_user
from conftest import UserBuilder
from helpers.apikeys import PreparedApikey
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.logs import UNKNOWN_OBJECT_ID
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.permissions.constants import (
    DEFAULT_APPLICABLE_PERMISSIONS,
    SUPERADMIN_APPLICABLE_PERMISSIONS,
)
from helpers.permissions.tests import BasePermissionTests
from helpers.users import PreparedUser

pytestmark = pytest.mark.anyio

UNKNOWN_SIGNUP_TOKEN = (
    "5620281609bbdc9796751a1cb1ac58efb27497b1fd14a0788faa83ada93e6048"
)


async def _wrap_signup_link_sending(func, expected_email: str) -> str:
    with patch("auditize.users.service.send_email") as mock:
        await func()
        mock.assert_called_once_with(
            expected_email,  # to
            callee.IsA(str),  # subject
            callee.Regex(".*/[0-9a-f]{64}.*"),  # body
        )
        match = re.search(r"([0-9a-f]{64})", mock.call_args[0][2])
        return match.group(1)


async def _assert_signup_token_validity(token: str):
    # this function does not intend to test the endpoint, but only
    # check that the token is valid
    client = HttpTestHelper.spawn()
    await client.assert_get_ok(f"/users/signup/{token}")


async def test_user_create(user_write_client: HttpTestHelper, dbm: DatabaseManager):
    data = PreparedUser.prepare_data()
    user_id = ""

    async def func():
        nonlocal user_id
        resp = await user_write_client.assert_post(
            "/users",
            json=data,
            expected_status_code=201,
            expected_json={"id": callee.IsA(str)},
        )
        user_id = resp.json()["id"]

    signup_token = await _wrap_signup_link_sending(func, data["email"])

    user = PreparedUser(user_id, data, dbm)
    await assert_collection(dbm.core_db.users, [user.expected_document()])

    await _assert_signup_token_validity(signup_token)


async def test_user_create_lang_fr(
    user_write_client: HttpTestHelper, dbm: DatabaseManager
):
    data = PreparedUser.prepare_data({"lang": "fr"})

    resp = await user_write_client.assert_post_created(
        "/users",
        json=data,
        expected_json={"id": callee.IsA(str)},
    )

    user = PreparedUser(resp.json()["id"], data, dbm)
    await assert_collection(dbm.core_db.users, [user.expected_document()])


async def test_user_create_missing_parameter(
    user_write_client: HttpTestHelper, dbm: DatabaseManager
):
    template = PreparedUser.prepare_data()
    for key in template:
        data = template.copy()
        del data[key]

        await user_write_client.assert_post_bad_request(
            "/users",
            json=data,
            expected_json={
                "message": "Invalid request",
                "validation_errors": [
                    {
                        "field": key,
                        "message": "Field required",
                    }
                ],
            },
        )


async def test_user_create_invalid_email(user_write_client: HttpTestHelper):
    await user_write_client.assert_post_bad_request(
        "/users",
        json={
            "email": "this_is_not_an_email",
            "first_name": "Another John",
            "last_name": "Another Doe",
        },
        expected_json={
            "message": "Invalid request",
            "validation_errors": [
                {
                    "field": "email",
                    "message": callee.Contains("not a valid email address"),
                }
            ],
        },
    )


async def test_user_create_unsupported_lang(user_write_client: HttpTestHelper):
    await user_write_client.assert_post_bad_request(
        "/users",
        json=PreparedUser.prepare_data({"lang": "de"}),
        expected_json={
            "message": "Invalid request",
            "validation_errors": [
                {
                    "field": "lang",
                    "message": callee.Contains("Input should be"),
                }
            ],
        },
    )


async def test_user_create_already_used_email(
    user_write_client: HttpTestHelper, user: PreparedUser
):
    await user_write_client.assert_post_constraint_violation(
        "/users",
        json={
            "email": user.data["email"],
            "first_name": "Another John",
            "last_name": "Another Doe",
        },
    )


async def test_user_create_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_post_forbidden(
        "/users", json=PreparedUser.prepare_data()
    )


async def test_user_update_multiple(
    user_write_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    data = {
        "first_name": "John Updated",
        "last_name": "Doe Updated",
        "email": "john.doe_updated@example.net",
        "lang": "fr",
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


async def test_user_update_unknown_id(user_write_client: HttpTestHelper):
    await user_write_client.assert_patch_not_found(
        f"/users/{UNKNOWN_OBJECT_ID}",
        json={"first_name": "John Updated"},
    )


async def test_user_update_already_used_email(
    user_write_client: HttpTestHelper, dbm: DatabaseManager
):
    user1 = await PreparedUser.create(user_write_client, dbm)
    user2 = await PreparedUser.create(user_write_client, dbm)

    await user_write_client.assert_patch_constraint_violation(
        f"/users/{user1.id}",
        json={"email": user2.data["email"]},
    )


async def test_user_update_forbidden(
    no_permission_client: HttpTestHelper, user: PreparedUser
):
    await no_permission_client.assert_patch_forbidden(
        f"/users/{user.id}", json={"first_name": "John Updated"}
    )


async def test_user_update_self(user_builder: UserBuilder):
    user = await user_builder(
        {
            "management": {
                "users": {"read": True, "write": True},
            }
        }
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_patch_forbidden(
            f"/users/{user.id}", json={"first_name": "John Updated"}
        )


async def test_user_get(user_read_client: HttpTestHelper, user: PreparedUser):
    await user_read_client.assert_get(
        f"/users/{user.id}",
        expected_status_code=200,
        expected_json=user.expected_api_response(),
    )


async def test_user_get_unknown_id(user_read_client: HttpTestHelper):
    await user_read_client.assert_get_not_found(f"/users/{UNKNOWN_OBJECT_ID}")


async def test_user_get_forbidden(
    no_permission_client: HttpTestHelper, user: PreparedUser
):
    await no_permission_client.assert_get_forbidden(f"/users/{user.id}")


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
            for user in sorted(users, key=lambda u: u.data["last_name"])
        ],
    )


@pytest.mark.parametrize("field", ["first_name", "last_name", "email"])
async def test_user_list_search(
    user_rw_client: HttpTestHelper,
    dbm: DatabaseManager,
    field: str,
):
    user_1 = await PreparedUser.create(
        user_rw_client,
        dbm,
        {
            "first_name": "Walter",
            "last_name": "White",
            "email": "walter.white@gmail.com",
        },
    )

    user_2 = await PreparedUser.create(
        user_rw_client,
        dbm,
        {
            "first_name": "Jesse",
            "last_name": "Pinkman",
            "email": "jesse.pinkman@hotmail.com",
        },
    )

    field_value = user_2.data[field]

    await user_rw_client.assert_get_ok(
        f"/users?q={field_value}",
        expected_json={
            "items": [user_2.expected_api_response()],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_user_list_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_get_forbidden("/users")


async def test_user_delete(
    user_write_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    await user_write_client.assert_delete(f"/users/{user.id}", expected_status_code=204)

    await assert_collection(dbm.core_db.users, [])


async def test_user_delete_unknown_id(user_write_client: HttpTestHelper):
    await user_write_client.assert_delete_not_found(f"/users/{UNKNOWN_OBJECT_ID}")


async def test_user_delete_forbidden(
    no_permission_client: HttpTestHelper, user: PreparedUser
):
    await no_permission_client.assert_delete_forbidden(f"/users/{user.id}")


async def test_user_delete_self(user_builder: UserBuilder):
    user = await user_builder(
        {
            "management": {
                "users": {"read": True, "write": True},
            }
        }
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_delete_forbidden(f"/users/{user.id}")


async def test_user_delete_last_superadmin(
    user_write_client: HttpTestHelper, user_builder: UserBuilder
):
    superadmin = await user_builder({"is_superadmin": True})
    await user_write_client.assert_delete_constraint_violation(
        f"/users/{superadmin.id}"
    )


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
    await anon_client.assert_get_not_found(
        f"/users/signup/{await user.signup_token}",
    )


async def test_user_signup_unknown(anon_client: HttpTestHelper):
    await anon_client.assert_get_not_found(
        f"/users/signup/{UNKNOWN_SIGNUP_TOKEN}",
    )


async def _assert_user_password_validity(email: str, password: str):
    client = HttpTestHelper.spawn()
    await client.assert_post_ok(
        "/auth/user/login",
        json={"email": email, "password": password},
    )


async def test_user_signup_set_password_fresh_user(
    anon_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    await anon_client.assert_post_no_content(
        f"/users/signup/{await user.signup_token}",
        json={"password": "new_password"},
    )

    await assert_collection(
        dbm.core_db.users,
        [
            user.expected_document(
                {"password_hash": callee.IsA(str), "signup_token": None}
            )
        ],
    )

    await _assert_user_password_validity(user.email, "new_password")


async def test_user_signup_set_password_after_forgot_password(
    user_builder: UserBuilder, dbm: DatabaseManager
):
    user = await user_builder({})

    async def func():
        await HttpTestHelper.spawn().assert_post_no_content(
            "/users/forgot-password",
            json={"email": user.email},
        )

    signup_token = await _wrap_signup_link_sending(func, user.email)

    await HttpTestHelper.spawn().assert_post_no_content(
        f"/users/signup/{signup_token}",
        json={"password": "new_password"},
    )

    await assert_collection(
        dbm.core_db.users,
        [
            user.expected_document(
                {"password_hash": callee.IsA(str), "signup_token": None}
            )
        ],
    )

    await _assert_user_password_validity(user.email, "new_password")


async def test_user_signup_set_password_too_short(
    anon_client: HttpTestHelper, user: PreparedUser, dbm: DatabaseManager
):
    await anon_client.assert_post_bad_request(
        f"/users/signup/{await user.signup_token}",
        json={"password": "short"},
    )


async def test_user_signup_set_password_token_expired(
    anon_client: HttpTestHelper, user: PreparedUser
):
    await user.expire_signup_token()
    await anon_client.assert_post_not_found(
        f"/users/signup/{await user.signup_token}",
        json={"password": "new_password"},
    )


async def test_user_signup_set_password_token_unknown(anon_client: HttpTestHelper):
    await anon_client.assert_post_not_found(
        f"/users/signup/{UNKNOWN_SIGNUP_TOKEN}",
        json={"password": "new_password"},
    )


async def test_get_user_me(user_builder: UserBuilder):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get(
            "/users/me",
            expected_status_code=200,
            expected_json={
                "id": user.id,
                "first_name": user.data["first_name"],
                "last_name": user.data["last_name"],
                "lang": "en",
                "email": user.data["email"],
                "permissions": DEFAULT_APPLICABLE_PERMISSIONS,
            },
        )


async def test_get_user_me_superadmin(user_builder: UserBuilder):
    user = await user_builder({"is_superadmin": True})
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
                "lang": "en",
                "permissions": SUPERADMIN_APPLICABLE_PERMISSIONS,
            },
        )


async def test_get_user_me_unauthorized(anon_client: HttpTestHelper):
    await anon_client.assert_get_unauthorized("/users/me")


async def test_get_user_me_as_apikey(apikey_client: HttpTestHelper):
    await apikey_client.assert_get_forbidden("/users/me")


async def test_update_user_me_lang(user_builder: UserBuilder, dbm: DatabaseManager):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_patch_ok(
            "/users/me",
            json={
                "lang": "fr",
            },
            expected_json={
                "id": user.id,
                "first_name": user.data["first_name"],
                "last_name": user.data["last_name"],
                "lang": "fr",
                "email": user.data["email"],
                "permissions": DEFAULT_APPLICABLE_PERMISSIONS,
            },
        )

    await assert_collection(dbm.core_db.users, [user.expected_document({"lang": "fr"})])


async def test_update_user_me_password(
    user_builder: UserBuilder, anon_client: HttpTestHelper, dbm: DatabaseManager
):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_patch_ok(
            "/users/me",
            json={
                "password": "new_password",
            },
        )

    # Make sure we don't have side effects in DB
    await assert_collection(dbm.core_db.users, [user.expected_document()])

    # Make sure the new password actually works
    await anon_client.assert_post_ok(
        "/auth/user/login",
        json={"email": user.email, "password": "new_password"},
    )


async def test_update_user_me_forbidden_field(
    user_builder: UserBuilder, dbm: DatabaseManager
):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_patch_ok(
            "/users/me",
            json={"first_name": "I cannot do this"},
        )

    # ensure nothing changed
    await assert_collection(dbm.core_db.users, [user.expected_document()])


async def test_update_user_me_as_unauthorized(anon_client: HttpTestHelper):
    await anon_client.assert_patch_unauthorized(
        "/users/me",
        json={
            "lang": "fr",
        },
    )


async def test_update_user_me_as_apikey(apikey_client: HttpTestHelper):
    await apikey_client.assert_patch_forbidden(
        "/users/me",
        json={
            "lang": "fr",
        },
    )


async def test_user_forgot_password_with_enrolled_user(
    user_builder: UserBuilder, dbm: DatabaseManager
):
    user = await user_builder({})

    async def func():
        await HttpTestHelper.spawn().assert_post_no_content(
            "/users/forgot-password",
            json={"email": user.email},
        )

    signup_token = await _wrap_signup_link_sending(func, user.email)

    await _assert_signup_token_validity(signup_token)


async def test_user_forgot_password_with_not_yet_enrolled_user(
    user: PreparedUser, dbm: DatabaseManager
):
    async def func():
        await HttpTestHelper.spawn().assert_post_no_content(
            "/users/forgot-password",
            json={"email": user.email},
        )

    signup_token = await _wrap_signup_link_sending(func, user.email)

    await _assert_signup_token_validity(signup_token)


async def test_user_forgot_password_with_enrolled_user_and_pending_forgot_password(
    user_builder: UserBuilder, dbm: DatabaseManager
):
    user = await user_builder({})

    async def func():
        await HttpTestHelper.spawn().assert_post_no_content(
            "/users/forgot-password",
            json={"email": user.email},
        )

    # For an already enrolled user, make sure we can trigger a second
    # forgot password request
    signup_token_1 = await _wrap_signup_link_sending(func, user.email)
    signup_token_2 = await _wrap_signup_link_sending(func, user.email)

    await _assert_signup_token_validity(signup_token_2)


class TestPermissions(BasePermissionTests):
    @property
    def base_path(self):
        return "/users"

    def get_principal_collection(self, dbm: DatabaseManager):
        return dbm.core_db.users

    async def inject_grantor(
        self, dbm: DatabaseManager, permissions=None
    ) -> PreparedApikey:
        return await PreparedApikey.inject_into_db(
            dbm,
            PreparedApikey.prepare_model(permissions=permissions),
        )

    def prepare_assignee_data(self, permissions=None):
        return PreparedUser.prepare_data(permissions)

    async def create_assignee(
        self, client: HttpTestHelper, dbm: DatabaseManager, data=None
    ) -> PreparedUser:
        return await PreparedUser.create(client, dbm, data)

    def rebuild_assignee_from_response(
        self, resp: Response, data: dict, dbm: DatabaseManager
    ) -> PreparedUser:
        return PreparedUser(resp.json()["id"], data, dbm)
