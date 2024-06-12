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
            "translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATION},
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
            "translations": {"fr": PreparedLogI18nProfile.FRENCH_TRANSLATION},
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
                "fr": PreparedLogI18nProfile.FRENCH_TRANSLATION,
                "en": PreparedLogI18nProfile.ENGLISH_TRANSLATION,
            },
        },
        dbm,
    )


async def test_log_i18n_profile_create_partial_lang_translations(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await _test_create_log_i18n_profile(
        repo_write_client,
        {
            "name": "i18n",
            "translations": {
                "en": {
                    "action_type": {
                        "action_type_1": "action_type_1 EN",
                    },
                    "action_category": {
                        "action_1": "action_1 EN",
                    },
                },
            },
        },
        dbm,
    )


async def test_log_i18n_profile_create_invalid_nesting_group(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await repo_write_client.assert_post_bad_request(
        "/log-i18n-profiles",
        json={
            "name": "i18n",
            "translations": {
                "en": {
                    "invalid_group": {},
                },
            },
        },
    )


async def test_log_i18n_profile_create_missing_name(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await repo_write_client.assert_post_bad_request(
        "/log-i18n-profiles",
        json={},
    )


async def test_log_i18n_profile_create_name_already_used(
    repo_write_client: HttpTestHelper, dbm: DatabaseManager
):
    await PreparedLogI18nProfile.create(dbm, {"name": "i18n"})

    await repo_write_client.assert_post_constraint_violation(
        "/log-i18n-profiles",
        json={
            "name": "i18n",
        },
    )


async def test_log_i18n_profile_create_forbidden(
    repo_read_client: HttpTestHelper, dbm: DatabaseManager
):
    await repo_read_client.assert_post_forbidden(
        "/log-i18n-profiles",
        json={
            "name": "i18n",
        },
    )
