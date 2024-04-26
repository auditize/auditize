from datetime import datetime
from jose import jwt

from auditize.auth import get_authenticated
from auditize.users.service import generate_jwt_token_payload
from auditize.common.db import DatabaseManager
from auditize.common.exceptions import AuthenticationFailure

import pytest
from unittest.mock import patch

from helpers.integrations import PreparedIntegration
from helpers.users import PreparedUser
from helpers.http import make_http_request, HttpTestHelper

pytestmark = pytest.mark.anyio


async def test_auth_no_auth(dbm: DatabaseManager, integration: PreparedIntegration):
    request = make_http_request()

    with pytest.raises(AuthenticationFailure):
        await get_authenticated(dbm, request)


async def test_auth_integration(dbm: DatabaseManager, integration: PreparedIntegration):
    request = make_http_request(
        headers={
            "Authorization": f"Bearer {integration.token}"
        }
    )
    authenticated = await get_authenticated(dbm, request)
    assert authenticated
    assert authenticated.name == integration.data["name"]


async def test_auth_invalid_authorization_header(dbm: DatabaseManager, integration: PreparedIntegration):
    request = make_http_request(
        headers={
            "Authorization": f"This is not a valid authorization header we recognize"
        }
    )

    with pytest.raises(AuthenticationFailure, match="not a Bearer token"):
        await get_authenticated(dbm, request)


async def test_auth_invalid_authorization_bearer(dbm: DatabaseManager, integration: PreparedIntegration):
    request = make_http_request(
        headers={
            # A syntactically correct Bearer token, but not a valid one:
            "Authorization": f"Bearer intgr-BOg6yxarq9oJ-y98VOMvy4gERijPxtcjta6YVxKiAaU"
        }
    )
    with pytest.raises(AuthenticationFailure, match="Invalid integration token"):
        await get_authenticated(dbm, request)


async def test_auth_user(dbm: DatabaseManager, client: HttpTestHelper):
    user = await PreparedUser.inject_into_db(dbm)
    session_token = await user.get_session_token(client)

    request = make_http_request(
        headers={
            "Cookie": f"token={session_token}"
        }
    )
    authenticated = await get_authenticated(dbm, request)
    assert authenticated
    assert authenticated.name == user.data["email"]


async def test_auth_user_invalid_session_token_syntax(dbm: DatabaseManager):
    request = make_http_request(
        headers={
            "Cookie": f"token=INVALID_TOKEN"
        }
    )
    with pytest.raises(AuthenticationFailure, match="Cannot decode JWT token"):
        await get_authenticated(dbm, request)


async def test_auth_user_invalid_session_token_bad_signature(dbm: DatabaseManager):
    user = await PreparedUser.inject_into_db(dbm)

    # Prepare a valid JWT session token but sign with a different key
    jwt_payload, _ = generate_jwt_token_payload(user.data["email"])
    jwt_token = jwt.encode(jwt_payload, "agreatsigningkey", algorithm="HS256")

    request = make_http_request(
        headers={
            "Cookie": f"token={jwt_token}"
        }
    )

    with pytest.raises(AuthenticationFailure, match="Cannot decode JWT token"):
        await get_authenticated(dbm, request)


async def test_auth_user_invalid_session_token_expired(dbm: DatabaseManager, client: HttpTestHelper):
    user = await PreparedUser.inject_into_db(dbm)

    # Mock the current time to be 2024-01-01 to generate an already expired token
    with patch("auditize.users.service.now", lambda: datetime.fromisoformat("2024-01-01T00:00:00Z")):
        resp = await user.log_in(client)

    # Since the cookie is expired, we cannot not normally get it from resp.cookies, we have to do it
    # manually from the headers
    cookie_key_value_pair = resp.headers["Set-Cookie"].split(";")[0]
    session_token = cookie_key_value_pair.split("=")[1]

    request = make_http_request(
        headers={
            "Cookie": f"token={session_token}"
        }
    )

    with pytest.raises(AuthenticationFailure, match="JWT token expired"):
        await get_authenticated(dbm, request)
