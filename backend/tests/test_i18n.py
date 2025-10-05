import re

import pytest

from auditize.auth.authorizer import get_authenticated
from auditize.database.dbm import open_db_session
from auditize.i18n import get_request_lang, t
from conftest import UserBuilder
from helpers.http import HttpTestHelper, make_http_request

pytestmark = pytest.mark.anyio


async def test_i18n_detect_default(client: HttpTestHelper):
    request = make_http_request()
    assert get_request_lang(request) == "en"


async def test_i18n_detect_query_param(client: HttpTestHelper):
    request = make_http_request(query_params={"lang": "fr"})
    assert get_request_lang(request) == "fr"


async def test_i18n_detect_query_param_unsupported(client: HttpTestHelper):
    request = make_http_request(query_params={"lang": "it"})
    assert get_request_lang(request) == "en"


async def test_i18n_detect_user(user_builder: UserBuilder, client: HttpTestHelper):
    user = await user_builder({}, lang="fr")
    session_token = await user.get_session_token(client)

    request = make_http_request(headers={"Cookie": f"session={session_token}"})
    async with open_db_session() as session:
        await get_authenticated(session, request)
    lang = get_request_lang(request)
    assert lang == "fr"


async def test_i18n_detect_priority(user_builder: UserBuilder, client: HttpTestHelper):
    user = await user_builder({}, lang="fr")
    session_token = await user.get_session_token(client)

    request = make_http_request(
        headers={"Cookie": f"session={session_token}"}, query_params={"lang": "en"}
    )
    async with open_db_session() as session:
        await get_authenticated(session, request)
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


def test_i18n_translations():
    master_translations = t._translations["en"]
    for lang in ("fr",):
        translations = t._translations[lang]
        # Test that we have the exact same keys in all languages
        assert set(translations) == set(master_translations)
        # Test that variables within translations are identical
        for key in master_translations:
            assert re.findall(r"\{(.+)\}", translations[key]) == re.findall(
                r"\{(.+)\}", master_translations[key]
            ), f"Key {key!r} has different variables in {lang!r}"
