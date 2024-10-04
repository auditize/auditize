import json

import pytest

from auditize import __version__
from auditize.__main__ import async_main
from auditize.database import get_dbm
from helpers.http import HttpTestHelper
from helpers.user import PreparedUser

pytestmark = pytest.mark.anyio


async def test_bootstrap_default_superadmin_empty_db():
    await async_main(["bootstrap-default-superadmin"])
    client = HttpTestHelper.spawn()
    resp = await client.assert_post_ok(
        "/auth/user/login",
        json={"email": "super.admin@example.net", "password": "auditize"},
    )
    assert resp.json()["permissions"]["is_superadmin"] is True


async def test_bootstrap_default_superadmin_not_empty_db(user: PreparedUser):
    assert await get_dbm().core_db.users.count_documents({}) == 1
    await async_main(["bootstrap-default-superadmin"])
    assert await get_dbm().core_db.users.count_documents({}) == 1


async def test_config(capsys):
    await async_main(["config"])
    # simply check that the output is valid JSON
    json.loads(capsys.readouterr().out)


async def test_openapi(capsys):
    await async_main(["openapi"])
    # simply check that the output is valid JSON
    json.loads(capsys.readouterr().out)


async def test_version(capsys):
    await async_main(["version"])
    assert __version__ in capsys.readouterr().out
