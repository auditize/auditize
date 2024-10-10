import json

import pytest

from auditize import __version__
from auditize.__main__ import async_main

pytestmark = pytest.mark.anyio


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
