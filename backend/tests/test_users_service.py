import time

from jose import jwt
from icecream import ic

from auditize.common.db import DatabaseManager
from auditize.users import service
from auditize.common.exceptions import AuthenticationFailure
from auditize.common.config import get_config

import pytest
import callee

from helpers.users import PreparedUser

pytestmark = pytest.mark.anyio


async def test_user_log_in(dbm: DatabaseManager):
    now = int(time.time())
    config = get_config()
    user = await PreparedUser.inject_into_db(dbm)
    token, expires_at = await service.user_log_in(dbm, user.email, user.password)
    ic(token, expires_at)
    assert expires_at.timestamp() > now
    payload = jwt.decode(token, config.user_token_signing_key, algorithms=["HS256"])
    ic(payload)
    assert payload == {
        "sub": f"user_email:{user.email}",
        "exp": callee.GreaterOrEqual(now),
    }


async def test_user_log_in_unknown_email(dbm: DatabaseManager):
    with pytest.raises(AuthenticationFailure):
        await service.user_log_in(dbm, "unknown.guy@example.net", "somepassword")


async def test_user_log_in_wrong_password(dbm: DatabaseManager):
    user = await PreparedUser.inject_into_db(dbm)
    with pytest.raises(AuthenticationFailure):
        await service.user_log_in(dbm, user.email, "wrongpassword")
