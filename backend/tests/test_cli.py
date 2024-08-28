import json
from unittest.mock import patch

import pytest

from auditize.__main__ import main
from auditize.database import get_dbm
from helpers.http import HttpTestHelper
from helpers.user import PreparedUser

pytestmark = pytest.mark.anyio


async def test_empty_db():
    await main(["bootstrap-default-superadmin"])
    client = HttpTestHelper.spawn()
    resp = await client.assert_post_ok(
        "/auth/user/login",
        json={"email": "super.admin@example.net", "password": "auditize"},
    )
    assert resp.json()["permissions"]["is_superadmin"] is True


async def test_not_empty_db(user: PreparedUser):
    assert await get_dbm().core_db.users.count_documents({}) == 1
    await main(["bootstrap-default-superadmin"])
    assert await get_dbm().core_db.users.count_documents({}) == 1


async def test_config(capsys):
    await main(["config"])
    # simply check that the output is valid JSON
    json.loads(capsys.readouterr().out)


async def test_openapi(capsys):
    await main(["openapi"])
    # simply check that the output is valid JSON
    json.loads(capsys.readouterr().out)
