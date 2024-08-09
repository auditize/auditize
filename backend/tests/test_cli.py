from unittest.mock import patch

import pytest

from auditize.__main__ import main
from auditize.database import DatabaseManager
from conftest import dbm as dbm_fixt
from helpers.http import HttpTestHelper
from helpers.user import PreparedUser

pytestmark = pytest.mark.anyio


@pytest.fixture()
def dbm(dbm_fixt):
    # Override dbm fixture from conftest to also patch auditize.__main__.get_dbm
    with patch("auditize.__main__.get_dbm", lambda: dbm_fixt):
        yield dbm_fixt


async def test_empty_db(dbm: DatabaseManager):
    await main(["bootstrap_superadmin"])
    client = HttpTestHelper.spawn()
    resp = await client.assert_post_ok(
        "/auth/user/login",
        json={"email": "super.admin@example.net", "password": "auditize"},
    )
    assert resp.json()["permissions"]["is_superadmin"] is True


async def test_not_empty_db(dbm: DatabaseManager, user: PreparedUser):
    assert await dbm.core_db.users.count_documents({}) == 1
    await main(["bootstrap_superadmin"])
    assert await dbm.core_db.users.count_documents({}) == 1
