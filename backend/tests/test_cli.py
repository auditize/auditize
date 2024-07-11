from unittest.mock import patch

import pytest

from auditize.__main__ import main
from auditize.database import DatabaseManager
from helpers.http import create_http_client
from helpers.users import PreparedUser

pytestmark = pytest.mark.anyio


async def test_empty_db(dbm: DatabaseManager):
    with patch("auditize.__main__.get_dbm", lambda: dbm):
        await main(["bootstrap_superadmin"])
    client = create_http_client()
    resp = await client.assert_post_ok(
        "/auth/user/login",
        json={"email": "super.admin@example.net", "password": "auditize"},
    )
    assert resp.json()["permissions"]["is_superadmin"] is True


async def test_not_empty_db(dbm: DatabaseManager, user: PreparedUser):
    assert await dbm.core_db.users.count_documents({}) == 1
    with patch("auditize.__main__.get_dbm", lambda: dbm):
        await main(["bootstrap_superadmin"])
    assert await dbm.core_db.users.count_documents({}) == 1
