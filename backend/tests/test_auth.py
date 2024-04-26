from auditize.auth import get_authenticated
from auditize.common.db import DatabaseManager

import pytest

from helpers.integrations import PreparedIntegration
from helpers.http import make_http_request

pytestmark = pytest.mark.anyio


async def test_auth_no_auth(dbm: DatabaseManager, integration: PreparedIntegration):
    request = make_http_request()
    authenticated = await get_authenticated(dbm, request)
    assert authenticated is None


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
    authenticated = await get_authenticated(dbm, request)
    assert authenticated is None


async def test_auth_invalid_authorization_bearer(dbm: DatabaseManager, integration: PreparedIntegration):
    request = make_http_request(
        headers={
            # A syntactically correct Bearer token, but not a valid one:
            "Authorization": f"Bearer intgr-BOg6yxarq9oJ-y98VOMvy4gERijPxtcjta6YVxKiAaU"
        }
    )
    authenticated = await get_authenticated(dbm, request)
    assert authenticated is None
