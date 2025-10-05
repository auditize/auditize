import pytest

from auditize.i18n import Lang
from auditize.log_i18n_profile.models import LogLabels
from auditize.log_i18n_profile.service import translate
from auditize.log_i18n_profile.sql_models import LogI18nProfile, LogTranslation
from conftest import RepoBuilder
from helpers.http import HttpTestHelper
from helpers.log import UNKNOWN_UUID
from helpers.log_i18n_profile import PreparedLogI18nProfile
from helpers.pagination import do_test_page_pagination_common_scenarios

pytestmark = pytest.mark.anyio


async def _test_create_log_i18n_profile(client: HttpTestHelper, data: dict):
    await client.assert_post_created(
        "/log-i18n-profiles",
        json=data,
        expected_json=PreparedLogI18nProfile.build_expected_api_response(data),
    )


async def test_log_i18n_profile_create_empty(repo_write_client: HttpTestHelper):
    await _test_create_log_i18n_profile(repo_write_client, {"name": "i18n"})


async def test_log_i18n_profile_create_english(repo_write_client: HttpTestHelper):
    await _test_create_log_i18n_profile(
        repo_write_client,
        {
            "name": "i18n",
            "translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATION},
        },
    )


async def test_log_i18n_profile_create_french(repo_write_client: HttpTestHelper):
    await _test_create_log_i18n_profile(
        repo_write_client,
        {
            "name": "i18n",
            "translations": {"fr": PreparedLogI18nProfile.FRENCH_TRANSLATION},
        },
    )


async def test_log_i18n_profile_create_all_languages(repo_write_client: HttpTestHelper):
    await _test_create_log_i18n_profile(
        repo_write_client,
        {
            "name": "i18n",
            "translations": {
                "fr": PreparedLogI18nProfile.FRENCH_TRANSLATION,
                "en": PreparedLogI18nProfile.ENGLISH_TRANSLATION,
            },
        },
    )


async def test_log_i18n_profile_create_partial_lang_translations(
    repo_write_client: HttpTestHelper,
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
    )


async def test_log_i18n_profile_create_invalid_nesting_group(
    repo_write_client: HttpTestHelper,
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


async def test_log_i18n_profile_create_missing_name(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_post_bad_request(
        "/log-i18n-profiles",
        json={},
    )


async def test_log_i18n_profile_create_name_already_used(
    repo_write_client: HttpTestHelper,
):
    await PreparedLogI18nProfile.create({"name": "i18n"})

    await repo_write_client.assert_post_constraint_violation(
        "/log-i18n-profiles",
        json={
            "name": "i18n",
        },
    )


async def test_log_i18n_profile_create_forbidden(repo_read_client: HttpTestHelper):
    await repo_read_client.assert_post_forbidden(
        "/log-i18n-profiles",
        json={
            "name": "i18n",
        },
    )


async def test_log_i18n_profile_update_name(repo_write_client: HttpTestHelper):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18n",
            "translations": {
                "en": PreparedLogI18nProfile.ENGLISH_TRANSLATION,
                "fr": PreparedLogI18nProfile.FRENCH_TRANSLATION,
            },
        },
    )
    await repo_write_client.assert_patch_ok(
        f"/log-i18n-profiles/{profile.id}",
        json={
            "name": "i18n updated",
        },
        expected_json=profile.expected_api_response({"name": "i18n updated"}),
    )


async def test_log_i18n_profile_update_add_translation(
    repo_write_client: HttpTestHelper,
):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18n",
            "translations": {
                "en": PreparedLogI18nProfile.ENGLISH_TRANSLATION,
            },
        },
    )
    await repo_write_client.assert_patch_ok(
        f"/log-i18n-profiles/{profile.id}",
        json={
            "translations": {
                "fr": PreparedLogI18nProfile.FRENCH_TRANSLATION,
            },
        },
        expected_json=profile.expected_api_response(
            {
                "translations": {
                    "en": PreparedLogI18nProfile.ENGLISH_TRANSLATION,
                    "fr": PreparedLogI18nProfile.FRENCH_TRANSLATION,
                }
            }
        ),
    )


async def test_log_i18n_profile_update_remove_translation(
    repo_write_client: HttpTestHelper,
):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18n",
            "translations": {
                "en": PreparedLogI18nProfile.ENGLISH_TRANSLATION,
                "fr": PreparedLogI18nProfile.FRENCH_TRANSLATION,
            },
        },
    )
    await repo_write_client.assert_patch_ok(
        f"/log-i18n-profiles/{profile.id}",
        json={
            "translations": {"fr": None},
        },
        expected_json=profile.expected_api_response(
            {
                "translations": {
                    "en": PreparedLogI18nProfile.ENGLISH_TRANSLATION,
                    # French translation must be removed
                }
            }
        ),
    )


async def test_log_i18n_profile_update_existing_translation(
    repo_write_client: HttpTestHelper,
):
    profile = await PreparedLogI18nProfile.create(
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
                # NB: French translation won't be updated and must remain the same
                "fr": {
                    "action_type": {
                        "action_type_1": "action_type_1 FR",
                    },
                    "action_category": {
                        "action_1": "action_1 FR",
                    },
                },
            },
        },
    )
    await repo_write_client.assert_patch_ok(
        f"/log-i18n-profiles/{profile.id}",
        json={
            "translations": {
                # A language translation completely overrides the existing one
                "en": {
                    "action_type": {
                        "action_type_1": "action_type_1 EN updated",
                    },
                },
            },
        },
        expected_json=profile.expected_api_response(
            {
                "translations": {
                    "en": {
                        **PreparedLogI18nProfile.EMPTY_TRANSLATION,
                        "action_type": {"action_type_1": "action_type_1 EN updated"},
                    },
                    "fr": {
                        **PreparedLogI18nProfile.EMPTY_TRANSLATION,
                        "action_type": {
                            "action_type_1": "action_type_1 FR",
                        },
                        "action_category": {
                            "action_1": "action_1 FR",
                        },
                    },
                }
            }
        ),
    )


async def test_log_i18n_profile_update_add_invalid_lang(
    repo_write_client: HttpTestHelper,
):
    profile = await PreparedLogI18nProfile.create()
    await repo_write_client.assert_patch_bad_request(
        f"/log-i18n-profiles/{profile.id}",
        json={
            "translations": {"es": {}},
        },
    )


async def test_log_i18n_profile_update_name_already_used(
    repo_write_client: HttpTestHelper,
):
    profile_1 = await PreparedLogI18nProfile.create({"name": "i18n"})
    profile_2 = await PreparedLogI18nProfile.create()

    await repo_write_client.assert_patch_constraint_violation(
        f"/log-i18n-profiles/{profile_2.id}",
        json={
            "name": "i18n",
        },
    )


async def test_log_i18n_profile_update_forbidden(repo_read_client: HttpTestHelper):
    profile = await PreparedLogI18nProfile.create()

    await repo_read_client.assert_patch_forbidden(
        f"/log-i18n-profiles/{profile.id}",
        json={
            "name": "i18n",
        },
    )


async def test_log_i18n_profile_update_not_found(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_patch_not_found(
        f"/log-i18n-profiles/{UNKNOWN_UUID}",
        json={
            "name": "i18n",
        },
    )


async def test_log_i18n_profile_get_empty(repo_read_client: HttpTestHelper):
    profile = await PreparedLogI18nProfile.create()
    await repo_read_client.assert_get_ok(
        f"/log-i18n-profiles/{profile.id}",
        expected_json=profile.expected_api_response(),
    )


async def test_log_i18n_profile_get_with_translations(repo_read_client: HttpTestHelper):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18n",
            "translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATION},
        },
    )
    await repo_read_client.assert_get_ok(
        f"/log-i18n-profiles/{profile.id}",
        expected_json=profile.expected_api_response(),
    )


async def test_log_i18n_profile_get_not_found(repo_read_client: HttpTestHelper):
    await repo_read_client.assert_get_not_found(
        f"/log-i18n-profiles/{UNKNOWN_UUID}",
    )


async def test_log_i18n_profile_get_forbidden(repo_write_client: HttpTestHelper):
    profile = await PreparedLogI18nProfile.create()

    await repo_write_client.assert_get_forbidden(
        f"/log-i18n-profiles/{profile.id}",
    )


async def test_log_i18n_profile_translation_get_empty(repo_read_client: HttpTestHelper):
    profile = await PreparedLogI18nProfile.create()
    await repo_read_client.assert_get_ok(
        f"/log-i18n-profiles/{profile.id}/translations/en",
        expected_json=PreparedLogI18nProfile.EMPTY_TRANSLATION,
    )


async def test_log_i18n_profile_translation_get_with_translation(
    repo_read_client: HttpTestHelper,
):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18n",
            "translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATION},
        },
    )
    await repo_read_client.assert_get_ok(
        f"/log-i18n-profiles/{profile.id}/translations/en",
        expected_json=PreparedLogI18nProfile.ENGLISH_TRANSLATION,
    )


async def test_log_i18n_profile_translation_get_not_found(
    repo_read_client: HttpTestHelper,
):
    await repo_read_client.assert_get_not_found(
        f"/log-i18n-profiles/{UNKNOWN_UUID}/translations/en",
    )


async def test_log_i18n_profile_translation_get_forbidden(
    repo_write_client: HttpTestHelper,
):
    profile = await PreparedLogI18nProfile.create()

    await repo_write_client.assert_get_forbidden(
        f"/log-i18n-profiles/{profile.id}/translations/en",
    )


async def test_log_i18n_profile_list(repo_read_client: HttpTestHelper):
    profiles = [
        await PreparedLogI18nProfile.create(
            PreparedLogI18nProfile.prepare_data(
                {"translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATION}}
            ),
        )
        for _ in range(5)
    ]

    await do_test_page_pagination_common_scenarios(
        repo_read_client,
        "/log-i18n-profiles",
        [
            profile.expected_api_response()
            for profile in sorted(profiles, key=lambda r: r.data["name"])
        ],
    )


async def test_log_i18n_profile_list_with_search(repo_read_client: HttpTestHelper):
    profiles = [
        await PreparedLogI18nProfile.create({"name": f"profile_{i}"}) for i in range(2)
    ]

    await repo_read_client.assert_get_ok(
        "/log-i18n-profiles?q=profile_1",
        expected_json={
            "items": [profiles[1].expected_api_response()],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_log_i18n_profile_list_forbidden(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_get_forbidden(
        "/log-i18n-profiles",
    )


async def test_log_i18n_profile_delete(
    repo_write_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
    superadmin_client,
):
    await repo_write_client.assert_delete_no_content(
        f"/log-i18n-profiles/{log_i18n_profile.id}"
    )
    await superadmin_client.assert_get_not_found(
        f"/log-i18n-profiles/{log_i18n_profile.id}"
    )


async def test_log_i18n_profile_delete_while_used_by_repo(
    repo_write_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
    repo_builder: RepoBuilder,
):
    await repo_builder({"log_i18n_profile_id": log_i18n_profile.id})

    await repo_write_client.assert_delete_constraint_violation(
        f"/log-i18n-profiles/{log_i18n_profile.id}"
    )


async def test_log_i18n_profile_delete_unknown_id(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_delete_not_found(
        f"/log-i18n-profiles/{UNKNOWN_UUID}"
    )


async def test_log_i18n_profile_delete_forbidden(
    no_permission_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
):
    await no_permission_client.assert_delete_forbidden(
        f"/log-i18n-profiles/{log_i18n_profile.id}"
    )


def test_get_log_value_translation():
    profile = LogI18nProfile(name="test")
    profile.translations.append(
        LogTranslation(
            lang=Lang.EN,
            labels=LogLabels(
                action_type={"user-login": "Authentification utilisateur"},
            ),
        )
    )
    assert (
        translate(profile, Lang.FR, "action_type", "user-login")
        == "Authentification utilisateur"
    )


def test_get_log_value_translation_without_log_i18n_profile():
    assert translate(None, Lang.FR, "action_type", "user-login") == "User Login"


def test_get_log_value_translation_unknown_key_type():
    profile = LogI18nProfile(name="test")
    profile.translations.append(LogTranslation(lang=Lang.FR, labels=LogLabels()))
    with pytest.raises(ValueError):
        translate(profile, Lang.FR, "unknown_key_type", "user-login")


async def test_get_log_value_translation_unknown_key():
    profile = LogI18nProfile(name="test")
    assert translate(profile, Lang.FR, "action_type", "user-login") == "User Login"


async def test_get_log_value_translation_english_fallback():
    profile = LogI18nProfile(name="test")
    profile.translations.append(
        LogTranslation(
            lang=Lang.EN,
            labels=LogLabels(
                action_type={"user-login": "User Authentication"},
            ),
        )
    )
    assert (
        translate(profile, Lang.FR, "action_type", "user-login")
        == "User Authentication"
    )
