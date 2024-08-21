from datetime import datetime
from unittest.mock import patch
from uuid import UUID

import pytest
from authlib.jose import jwt

from auditize.apikey.models import ApikeyUpdate
from auditize.apikey.service import update_apikey
from auditize.auth.authorizer import get_authenticated
from auditize.auth.jwt import (
    generate_access_token,
    generate_access_token_payload,
    generate_session_token_payload,
)
from auditize.exceptions import AuthenticationFailure
from auditize.permissions.models import Permissions
from conftest import ApikeyBuilder
from helpers.apikey import PreparedApikey
from helpers.http import HttpTestHelper, make_http_request
from helpers.user import PreparedUser

pytestmark = pytest.mark.anyio


async def test_auth_no_auth(apikey: PreparedApikey):
    request = make_http_request()

    with pytest.raises(AuthenticationFailure):
        await get_authenticated(request)


async def test_auth_apikey(apikey: PreparedApikey):
    request = make_http_request(headers={"Authorization": f"Bearer {apikey.key}"})
    authenticated = await get_authenticated(request)
    assert authenticated
    assert authenticated.name == apikey.data["name"]


async def test_auth_access_token(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({"is_superadmin": True})
    permissions = Permissions()
    permissions.management.repos.read = True
    access_token, _ = generate_access_token(UUID(apikey.id), permissions)

    request = make_http_request(headers={"Authorization": f"Bearer aat-{access_token}"})
    authenticated = await get_authenticated(request)
    assert authenticated
    assert authenticated.name == f"Access token for API key '{apikey.data['name']}'"
    assert authenticated.permissions == permissions


async def test_auth_access_token_invalid_syntax():
    request = make_http_request(headers={"Authorization": f"Bearer aat-INVALID_TOKEN"})
    with pytest.raises(AuthenticationFailure, match="Cannot decode JWT token"):
        await get_authenticated(request)


async def test_auth_access_token_bad_signature():
    apikey = await PreparedApikey.inject_into_db()

    # Prepare a valid JWT session token but sign with a different key
    jwt_payload, _ = generate_access_token_payload(UUID(apikey.id), Permissions())
    jwt_token = jwt.encode({"alg": "HS256"}, jwt_payload, key="agreatsigningkey")

    request = make_http_request(headers={"Authorization": f"Bearer aat-{jwt_token}"})

    with pytest.raises(AuthenticationFailure, match="Cannot decode JWT token"):
        await get_authenticated(request)


async def test_auth_access_token_expired():
    apikey = await PreparedApikey.inject_into_db()

    # Mock the current time to be 2024-01-01 to generate an already expired token
    with patch(
        "auditize.auth.jwt.now",
        lambda: datetime.fromisoformat("2024-01-01T00:00:00Z"),
    ):
        jwt_token, _ = generate_access_token(UUID(apikey.id), Permissions())

    request = make_http_request(headers={"Authorization": f"Bearer aat-{jwt_token}"})

    with pytest.raises(AuthenticationFailure, match="JWT token expired"):
        await get_authenticated(request)


async def test_auth_access_control_downgraded_apikey_permissions(
    apikey_builder: ApikeyBuilder,
):
    # first step, create a requesting using an access token with repos read permission from a superadmin apikey
    apikey = await apikey_builder({"is_superadmin": True})
    permissions = Permissions()
    permissions.management.repos.read = True
    access_token, _ = generate_access_token(UUID(apikey.id), permissions)
    request = make_http_request(headers={"Authorization": f"Bearer aat-{access_token}"})

    # second step, make sure the access token actually works
    await get_authenticated(request)

    # third step, downgrade the apikey permissions so the API key no longer have
    # any permissions at all
    apikey_update = ApikeyUpdate()
    apikey_update.permissions = Permissions()
    apikey_update.permissions.is_superadmin = False
    await update_apikey(UUID(apikey.id), apikey_update)

    # fourth step, try to authenticate with the access token
    # it must fail because the access token has now more permissions than the original API key
    with pytest.raises(
        AuthenticationFailure,
        match="The access token has more permissions than the original API key",
    ):
        await get_authenticated(request)


async def test_auth_invalid_authorization_header(apikey: PreparedApikey):
    request = make_http_request(
        headers={
            "Authorization": f"This is not a valid authorization header we recognize"
        }
    )

    with pytest.raises(AuthenticationFailure, match="not a Bearer"):
        await get_authenticated(request)


async def test_auth_invalid_authorization_bearer(apikey: PreparedApikey):
    request = make_http_request(
        headers={
            # A syntactically correct Bearer token, but not a valid one:
            "Authorization": f"Bearer intgr-BOg6yxarq9oJ-y98VOMvy4gERijPxtcjta6YVxKiAaU"
        }
    )
    with pytest.raises(AuthenticationFailure, match="Invalid bearer token"):
        await get_authenticated(request)


async def test_auth_user(client: HttpTestHelper):
    user = await PreparedUser.inject_into_db()
    session_token = await user.get_session_token(client)

    request = make_http_request(headers={"Cookie": f"session={session_token}"})
    authenticated = await get_authenticated(request)
    assert authenticated
    assert authenticated.name == user.data["email"]


async def test_auth_user_invalid_session_token_syntax():
    request = make_http_request(headers={"Cookie": f"session=INVALID_TOKEN"})
    with pytest.raises(AuthenticationFailure, match="Cannot decode JWT token"):
        await get_authenticated(request)


async def test_auth_user_invalid_session_token_bad_signature():
    user = await PreparedUser.inject_into_db()

    # Prepare a valid JWT session token but sign with a different key
    jwt_payload, _ = generate_session_token_payload(user.data["email"])
    jwt_token = jwt.encode({"alg": "HS256"}, jwt_payload, key="agreatsigningkey")

    request = make_http_request(headers={"Cookie": f"session={jwt_token}"})

    with pytest.raises(AuthenticationFailure, match="Cannot decode JWT token"):
        await get_authenticated(request)


async def test_auth_user_invalid_session_token_expired(client: HttpTestHelper):
    user = await PreparedUser.inject_into_db()

    # Mock the current time to be 2024-01-01 to generate an already expired token
    with patch(
        "auditize.auth.jwt.now",
        lambda: datetime.fromisoformat("2024-01-01T00:00:00Z"),
    ):
        resp = await user.log_in(client)

    # Since the cookie is expired, we cannot not normally get it from resp.cookies, we have to do it
    # manually from the headers
    cookie_key_value_pair = resp.headers["Set-Cookie"].split(";")[0]
    session_token = cookie_key_value_pair.split("=")[1]

    request = make_http_request(headers={"Cookie": f"session={session_token}"})

    with pytest.raises(AuthenticationFailure, match="JWT token expired"):
        await get_authenticated(request)


async def test_auth_http_request(anon_client: HttpTestHelper):
    await anon_client.assert_get_unauthorized("/repos")
