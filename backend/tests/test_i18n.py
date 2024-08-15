import pytest

from auditize.auth.authorizer import get_authenticated
from auditize.database import DatabaseManager
from auditize.i18n import t
from auditize.i18n.detection import get_request_lang
from conftest import UserBuilder
from helpers.http import HttpTestHelper, make_http_request

pytestmark = pytest.mark.anyio


async def test_i18n_detect_default(dbm: DatabaseManager, client: HttpTestHelper):
    request = make_http_request()
    assert get_request_lang(request) == "en"


async def test_i18n_detect_query_param(dbm: DatabaseManager, client: HttpTestHelper):
    request = make_http_request(query_params={"lang": "fr"})
    assert get_request_lang(request) == "fr"


async def test_i18n_detect_query_param_unsupported(
    dbm: DatabaseManager, client: HttpTestHelper
):
    request = make_http_request(query_params={"lang": "it"})
    assert get_request_lang(request) == "en"


async def test_i18n_detect_user(
    user_builder: UserBuilder, client: HttpTestHelper, dbm: DatabaseManager
):
    user = await user_builder({}, lang="fr")
    session_token = await user.get_session_token(client)

    request = make_http_request(headers={"Cookie": f"session={session_token}"})
    await get_authenticated(dbm, request)
    lang = get_request_lang(request)
    assert type(lang) is str
    assert lang == "fr"


async def test_i18n_detect_priority(
    user_builder: UserBuilder, client: HttpTestHelper, dbm: DatabaseManager
):
    user = await user_builder({}, lang="fr")
    session_token = await user.get_session_token(client)

    request = make_http_request(
        headers={"Cookie": f"session={session_token}"}, query_params={"lang": "en"}
    )
    await get_authenticated(dbm, request)
    assert get_request_lang(request) == "en"


def test_i18n_translation_ok():
    assert t("test") == "This is a test"
    assert t("test", lang="en") == "This is a test"
    assert t("test", lang="fr") == "Ceci est un test"


def test_i18n_translation_missing_lang():
    with pytest.raises(LookupError):
        assert t("test", lang="it")


def test_i18n_translation_missing_key():
    with pytest.raises(LookupError):
        assert t("unknown_key")


def test_i18n_translation_variable():
    assert t("test_var", {"var": "foo"}) == "This is a test with a variable foo"


def test_i18n_translation_variable_missing():
    with pytest.raises(LookupError):
        assert t("test_var")
