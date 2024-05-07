import time

import callee
import pytest
from icecream import ic
from jose import jwt

from auditize.auth.jwt import generate_session_token
from auditize.common.config import get_config

pytestmark = pytest.mark.anyio


async def test_generate_session_token():
    email = "john.doe@example.net"
    now = int(time.time())
    config = get_config()

    token, expires_at = generate_session_token(email)
    ic(token, expires_at)

    assert expires_at.timestamp() > now
    payload = jwt.decode(token, config.jwt_signing_key, algorithms=["HS256"])
    ic(payload)
    assert payload == {
        "sub": f"user_email:{email}",
        "exp": callee.GreaterOrEqual(now),
    }
