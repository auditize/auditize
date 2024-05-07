import time

import pytest
from icecream import ic

from auditize.common.db import DatabaseManager
from conftest import UserBuilder
from helpers.http import HttpTestHelper, get_cookie_by_name
from helpers.users import PreparedUser

pytestmark = pytest.mark.anyio


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


async def test_user_log_in_unknown_email(anon_client: HttpTestHelper):
    await anon_client.assert_unauthorized_post(
        "/users/login",
        json={"email": "unknown.guy@example.net", "password": "somepassword"},
    )


async def test_user_log_in_wrong_password(user_builder: UserBuilder):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_unauthorized_post(
            "/users/login",
            json={"email": user.email, "password": "wrongpassword"},
        )


async def test_user_log_out(user_builder: UserBuilder):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_post("/users/logout", expected_status_code=204)
        await client.assert_unauthorized_get("/users/me")
