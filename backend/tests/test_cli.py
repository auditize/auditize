import json
from contextlib import contextmanager
from datetime import datetime, timedelta
from unittest import mock

import pytest

from auditize.__main__ import async_main
from auditize.version import __version__
from conftest import RepoBuilder
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


async def test_bootstrap_superadmin_password_too_short(capsys):
    with _mock_getpass("short"):
        try:
            await async_main(
                ["bootstrap-superadmin", "john.doe@example.net", "John", "Doe"],
            )
        except EOFError:
            pass
    assert (
        "Password too short, it must be at least 8 characters long."
        in capsys.readouterr().err
    )


async def test_bootstrap_superadmin_password_too_short_retry_ok(capsys):
    with _mock_getpass("short", "longpassword", "longpassword"):
        await async_main(
            ["bootstrap-superadmin", "john.doe@example.net", "John", "Doe"],
        )

    await _assert_user_ok("john.doe@example.net", "John", "Doe", "longpassword")


async def test_purge_expired_logs_none(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo = await repo_builder({})
    await repo.create_log(superadmin_client)
    await async_main(["purge-expired-logs"])
    assert (await repo.db.logs.count_documents({})) == 1


async def test_purge_expired_logs_all(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo = await repo_builder({"retention_period": 30})
    await repo.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=90)
    )
    await async_main(["purge-expired-logs"])
    assert (await repo.db.logs.count_documents({})) == 0


async def test_purge_expired_logs_single(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo_1 = await repo_builder({"retention_period": 30})
    await repo_1.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=90)
    )

    repo_2 = await repo_builder({"retention_period": 30})
    await repo_2.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=90)
    )

    await async_main(["purge-expired-logs", repo_1.id])

    assert (await repo_1.db.logs.count_documents({})) == 0
    assert (await repo_2.db.logs.count_documents({})) == 1
