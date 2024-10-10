import json
from contextlib import contextmanager
from unittest import mock

import pytest

from auditize import __version__
from auditize.__main__ import async_main
from helpers.http import HttpTestHelper

pytestmark = pytest.mark.anyio


@contextmanager
def _mock_getpass(*args):
    args_iter = iter(args)

    def func(_):
        try:
            return next(args_iter)
        except StopIteration:
            # getpass raises EOFError when stdin is closed
            raise EOFError()

    with mock.patch("getpass.getpass", side_effect=func):
        yield


async def _assert_user_ok(email, first_name, last_name, password):
    client = HttpTestHelper.spawn()
    resp = await client.assert_post_ok(
        "/auth/user/login",
        json={"email": email, "password": password},
    )
    assert resp.json()["email"] == email
    assert resp.json()["first_name"] == first_name
    assert resp.json()["last_name"] == last_name
    assert resp.json()["lang"] == "en"
    assert resp.json()["permissions"]["is_superadmin"] == True


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


async def test_bootstrap_superadmin(capsys):
    with _mock_getpass("somegreatpassword", "somegreatpassword"):
        await async_main(
            ["bootstrap-superadmin", "john.doe@example.net", "John", "Doe"]
        )
    await _assert_user_ok("john.doe@example.net", "John", "Doe", "somegreatpassword")


async def test_bootstrap_superadmin_password_mismatch(capsys):
    with _mock_getpass("somegreatpassword", "incorrectconfirmation"):
        try:
            await async_main(
                ["bootstrap-superadmin", "john.doe@example.net", "John", "Doe"],
            )
        except EOFError:
            pass
    assert "Passwords do not match, please try again." in capsys.readouterr().err


async def test_bootstrap_superadmin_password_mismatch_retry_ok(capsys):
    with _mock_getpass(
        "somegreatpassword",
        "incorrectconfirmation",
        "somegreatpassword",
        "somegreatpassword",
    ):
        await async_main(
            ["bootstrap-superadmin", "john.doe@example.net", "John", "Doe"]
        )

    await _assert_user_ok("john.doe@example.net", "John", "Doe", "somegreatpassword")
