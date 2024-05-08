import time

import pytest
from icecream import ic

from auditize.auth.jwt import generate_session_token, get_user_email_from_session_token

pytestmark = pytest.mark.anyio


async def test_generation_and_check():
    email = "john.doe@example.net"
    now = int(time.time())

    token, expires_at = generate_session_token(email)
    ic(token, expires_at)

    assert expires_at.timestamp() > now
    actual_email = get_user_email_from_session_token(token)
    assert actual_email == email
