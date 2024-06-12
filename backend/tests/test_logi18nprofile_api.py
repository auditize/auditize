import callee
import pytest

from auditize.database import DatabaseManager
from helpers.database import assert_collection
from helpers.http import HttpTestHelper
from helpers.logi18nprofiles import PreparedLogI18nProfile

pytestmark = pytest.mark.anyio


async def _test_create_log_i18n_profile(
    client: HttpTestHelper, data: dict, dbm: DatabaseManager
):
    resp = await client.assert_post_created(
        "/log-i18n-profiles",
        json=data,
        expected_json={"id": callee.IsA(str)},
    )
    profile = PreparedLogI18nProfile(resp.json()["id"], data)
    await assert_collection(dbm.core_db.logi18nprofiles, [profile.expected_document()])


async def test_log_i18n_profile_create_empty(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await _test_create_log_i18n_profile(repo_write_client, {"name": "i18n"}, dbm)


async def test_log_i18n_profile_create_english(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await _test_create_log_i18n_profile(
        repo_write_client,
        {
            "name": "i18n",
            "translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATIONS},
        },
        dbm,
    )


async def test_log_i18n_profile_create_french(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await _test_create_log_i18n_profile(
        repo_write_client,
        {
            "name": "i18n",
            "translations": {"fr": PreparedLogI18nProfile.FRENCH_TRANSLATIONS},
        },
        dbm,
    )


async def test_log_i18n_profile_create_all_languages(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await _test_create_log_i18n_profile(
        repo_write_client,
        {
            "name": "i18n",
            "translations": {
                "fr": PreparedLogI18nProfile.FRENCH_TRANSLATIONS,
                "en": PreparedLogI18nProfile.ENGLISH_TRANSLATIONS,
            },
        },
        dbm,
    )
