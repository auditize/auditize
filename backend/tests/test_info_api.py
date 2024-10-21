from auditize.version import __version__
from conftest import ApikeyBuilder, UserBuilder
from helpers.http import HttpTestHelper


async def test_info_as_user(user_builder: UserBuilder):
    user = await user_builder({})
    async with user.client() as client:
        client: HttpTestHelper
        resp = await client.assert_get_ok("/info")

    assert resp.json() == {"auditize_version": __version__}


async def test_info_as_apikey(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({})
    async with apikey.client() as client:
        client: HttpTestHelper
        resp = await client.assert_get_ok("/info")

    assert resp.json() == {"auditize_version": __version__}


async def test_info_as_anonymous():
    client = HttpTestHelper.spawn()
    await client.assert_get_unauthorized("/info")
