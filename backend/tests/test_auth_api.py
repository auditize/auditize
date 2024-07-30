import time
from unittest.mock import patch

import callee
import pytest
from icecream import ic

from auditize.database import DatabaseManager
from conftest import ApikeyBuilder, UserBuilder
from helpers.http import HttpTestHelper, get_cookie_by_name
from helpers.permissions.constants import DEFAULT_APPLICABLE_PERMISSIONS
from helpers.users import PreparedUser
from helpers.utils import DATETIME_FORMAT

pytestmark = pytest.mark.anyio


def _assert_cookie(resp, now, expected_secure=True):
    cookie = get_cookie_by_name(resp, "session")
    assert cookie.name == "session"
    assert cookie.expires > now
    assert cookie.path == "/"
    assert cookie.secure == expected_secure
    assert cookie.value
    assert cookie.has_nonstandard_attr("HttpOnly")
    assert cookie.get_nonstandard_attr("SameSite") == "strict"


async def test_user_login(anon_client: HttpTestHelper, dbm: DatabaseManager):
    user = await PreparedUser.inject_into_db(dbm)
    now = int(time.time())
    resp = await anon_client.assert_post_ok(
        "/auth/user/login",
        json={"email": user.email, "password": user.password},
        expected_json={
            "id": user.id,
            "first_name": user.data["first_name"],
            "last_name": user.data["last_name"],
            "email": user.data["email"],
            "lang": "en",
            "permissions": DEFAULT_APPLICABLE_PERMISSIONS,
        },
    )
    ic(resp.cookies)
    _assert_cookie(resp, now)

    # test that the cookie auth actually works
    await anon_client.assert_get_ok("/users/me")


async def test_user_login_cookie_non_secure(
    anon_client: HttpTestHelper, dbm: DatabaseManager
):
    user = await PreparedUser.inject_into_db(dbm)
    now = int(time.time())
    with patch("auditize.auth.api.get_config") as mock:
        mock.return_value.cookie_secure = False
        resp = await anon_client.assert_post_ok(
            "/auth/user/login",
            json={"email": user.email, "password": user.password},
        )
    ic(resp.cookies)
    _assert_cookie(resp, now, expected_secure=False)

    # test that the cookie auth actually works
    await anon_client.assert_get_ok("/users/me")


async def test_user_login_unknown_email(anon_client: HttpTestHelper):
    await anon_client.assert_post_unauthorized(
        "/auth/user/login",
        json={"email": "unknown.guy@example.net", "password": "somepassword"},
    )


async def test_user_login_wrong_password(user_builder: UserBuilder):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_post_unauthorized(
            "/auth/user/login",
            json={"email": user.email, "password": "wrongpassword"},
        )


async def test_user_logout(user_builder: UserBuilder):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_post("/auth/user/logout", expected_status_code=204)
        await client.assert_get_unauthorized("/users/me")


async def test_access_token_empty_permissions(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({})
    async with apikey.client() as client:
        await client.assert_post_ok(
            "/auth/access-token",
            json={"permissions": {}},
            expected_json={
                "access_token": callee.String(),
                "expires_at": DATETIME_FORMAT,
            },
        )


async def test_access_token_authorized_permissions(
    apikey_builder: ApikeyBuilder, anon_client: HttpTestHelper
):
    apikey = await apikey_builder({"is_superadmin": True})
    async with apikey.client() as client:
        resp = await client.assert_post_ok(
            "/auth/access-token",
            json={"permissions": {"is_superadmin": True}},
            expected_json={
                "access_token": callee.String(),
                "expires_at": DATETIME_FORMAT,
            },
        )

    access_token = resp.json()["access_token"]

    # test that the access token actually works
    await anon_client.assert_get_ok(
        "/repos",
        headers={"Authorization": f"Bearer {access_token}"},
    )


async def test_access_token_unauthorized_permissions(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({})
    async with apikey.client() as client:
        await client.assert_post_forbidden(
            "/auth/access-token",
            json={"permissions": {"is_superadmin": True}},
        )


async def test_access_token_as_user(user_builder: ApikeyBuilder):
    user = await user_builder({})
    async with user.client() as client:
        await client.assert_post_forbidden(
            "/auth/access-token",
            json={"permissions": {}},
        )
