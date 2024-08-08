import time
import uuid

import pytest
from icecream import ic

from auditize.auth.jwt import (
    generate_access_token,
    generate_session_token,
    get_access_token_data,
    get_user_email_from_session_token,
)
from auditize.permissions.models import Permissions

pytestmark = pytest.mark.anyio


async def test_user_session_token():
    email = "john.doe@example.net"
    now = int(time.time())

    token, expires_at = generate_session_token(email)
    ic(token, expires_at)

    assert expires_at.timestamp() > now
    actual_email = get_user_email_from_session_token(token)
    assert actual_email == email


async def test_access_token():
    apikey_id = uuid.uuid4()
    permissions = Permissions()
    permissions.management.repos.read = True
    now = int(time.time())

    token, expires_at = generate_access_token(apikey_id, permissions)
    ic(token, expires_at)

    assert expires_at.timestamp() > now
    actual_apikey_id, actual_permissions = get_access_token_data(token)
    assert actual_apikey_id == apikey_id
    assert actual_permissions == permissions
