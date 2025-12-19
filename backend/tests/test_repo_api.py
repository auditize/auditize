from datetime import datetime
from typing import Awaitable, Callable

import pytest
from icecream import ic

from conftest import ApikeyBuilder, RepoBuilder, UserBuilder
from helpers import matchers
from helpers.apikey import PreparedApikey
from helpers.http import HttpTestHelper
from helpers.log import UNKNOWN_UUID
from helpers.log_i18n_profile import PreparedLogI18nProfile
from helpers.pagination import do_test_page_pagination_common_scenarios
from helpers.permissions.constants import DEFAULT_PERMISSIONS
from helpers.repo import PreparedRepo
from helpers.user import PreparedUser
from helpers.utils import strip_dict_keys

pytestmark = pytest.mark.anyio


async def _test_repo_create(
    client: HttpTestHelper, permissions_getter: Callable[[], Awaitable]
):
    data = {"name": "myrepo"}

    resp = await client.assert_post_created(
        "/repos",
        json=data,
        expected_json=PreparedRepo.build_expected_api_response(data),
    )
    repo_id = resp.json()["id"]

    # check that the authenticated user has read & write permissions on the new repo

    permissions = await permissions_getter()
    assert permissions["logs"]["repos"] == [
        {"repo_id": repo_id, "read": True, "write": True, "readable_entities": []}
    ]


async def _get_apikey_permissions(client: HttpTestHelper, user_id: str):
    resp = await client.assert_get_ok(f"/apikeys/{user_id}")
    return resp.json()["permissions"]


async def test_repo_create_as_apikey(
    apikey_builder: ApikeyBuilder, superadmin_client: HttpTestHelper
):
    apikey = await apikey_builder({"management": {"repos": {"write": True}}})

    async with apikey.client() as client:
        await _test_repo_create(
            client,
            lambda: _get_apikey_permissions(superadmin_client, apikey.id),
        )


async def _get_user_permissions(client: HttpTestHelper, user_id: str):
    resp = await client.assert_get_ok(f"/users/{user_id}")
    return resp.json()["permissions"]


async def test_repo_create_as_user(
    user_builder: UserBuilder, superadmin_client: HttpTestHelper
):
    user = await user_builder({"management": {"repos": {"write": True}}})

    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_create(
            client, lambda: _get_user_permissions(superadmin_client, user.id)
        )


@pytest.mark.parametrize("status", ["enabled", "readonly", "disabled"])
async def test_repo_create_with_explicit_status(
    superadmin_client: HttpTestHelper, status: str
):
    data = {"name": "myrepo", "status": status}

    await superadmin_client.assert_post_created(
        "/repos",
        json=data,
        expected_json=PreparedRepo.build_expected_api_response(data),
    )


async def test_repo_create_with_log_i18n_profile(
    superadmin_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
):
    data = {"name": "myrepo", "log_i18n_profile_id": log_i18n_profile.id}

    await superadmin_client.assert_post_created(
        "/repos",
        json=data,
        expected_json=PreparedRepo.build_expected_api_response(data),
    )


async def test_repo_create_with_retention_period(superadmin_client: HttpTestHelper):
    data = {
        "name": "myrepo",
        "retention_period": 30,
    }

    await superadmin_client.assert_post_created(
        "/repos",
        json=data,
        expected_json=PreparedRepo.build_expected_api_response(data),
    )


async def test_repo_create_missing_name(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_post_bad_request(
        "/repos",
        json={},
        expected_json={
            "message": "Invalid request",
            "localized_message": None,
            "validation_errors": [
                {
                    "field": "name",
                    "message": "Field required",
                }
            ],
        },
    )


async def test_repo_create_already_used_name(
    repo_write_client: HttpTestHelper, repo: PreparedRepo
):
    await repo_write_client.assert_post_constraint_violation(
        "/repos", json={"name": repo.data["name"]}
    )


async def test_repo_create_unknown_log_i18n_profile_id(
    repo_write_client: HttpTestHelper,
):
    await repo_write_client.assert_post_bad_request(
        "/repos",
        json={"name": "myrepo", "log_i18n_profile_id": UNKNOWN_UUID},
    )


async def test_repo_create_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_post_forbidden("/repos", json={"name": "myrepo"})


@pytest.mark.parametrize("field,value", [("name", "myrepo"), ("status", "disabled")])
async def test_repo_update(
    repo_write_client: HttpTestHelper,
    repo: PreparedRepo,
    field: str,
    value: str,
):
    await repo_write_client.assert_patch_ok(
        f"/repos/{repo.id}",
        json={field: value},
        expected_json=repo.expected_api_response({field: value}),
    )


async def test_repo_update_set_log_i18n_profile_id(
    repo_write_client: HttpTestHelper,
    repo: PreparedRepo,
    log_i18n_profile: PreparedLogI18nProfile,
):
    await repo_write_client.assert_patch_ok(
        f"/repos/{repo.id}",
        json={"log_i18n_profile_id": log_i18n_profile.id},
        expected_json=repo.expected_api_response(
            {"log_i18n_profile_id": log_i18n_profile.id}
        ),
    )


async def test_repo_update_unset_log_i18n_profile_id(
    repo_write_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
    repo_builder: RepoBuilder,
):
    repo = await repo_builder({"log_i18n_profile_id": log_i18n_profile.id})
    await repo_write_client.assert_patch_ok(
        f"/repos/{repo.id}",
        json={"log_i18n_profile_id": None},
        expected_json=repo.expected_api_response({"log_i18n_profile_id": None}),
    )


async def test_repo_update_set_retention_period(
    repo_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await repo_write_client.assert_patch_ok(
        f"/repos/{repo.id}",
        json={"retention_period": 30},
        expected_json=repo.expected_api_response({"retention_period": 30}),
    )


async def test_repo_update_unset_retention_period(
    repo_write_client: HttpTestHelper,
    repo_builder: RepoBuilder,
):
    repo = await repo_builder({"retention_period": 30})
    await repo_write_client.assert_patch_ok(
        f"/repos/{repo.id}",
        json={"retention_period": None},
        expected_json=repo.expected_api_response({"retention_period": None}),
    )


async def test_repo_update_empty_with_log_i18n_profile_id_already_set(
    repo_write_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
    repo_builder: RepoBuilder,
):
    repo = await repo_builder({"log_i18n_profile_id": log_i18n_profile.id})
    await repo_write_client.assert_patch_ok(
        f"/repos/{repo.id}",
        json={},
        expected_json=repo.expected_api_response(),
    )


async def test_repo_update_unknown_id(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_patch_not_found(
        f"/repos/{UNKNOWN_UUID}",
        json={"name": "Repo Updated"},
    )


async def test_repo_update_already_used_name(
    repo_write_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo_1 = await repo_builder({})
    repo_2 = await repo_builder({})

    await repo_write_client.assert_patch_constraint_violation(
        f"/repos/{repo_1.id}",
        json={"name": repo_2.data["name"]},
    )


async def test_repo_update_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_patch_forbidden(
        f"/repos/{repo.id}", json={"name": "Repo Updated"}
    )


async def test_repo_get(repo_read_client: HttpTestHelper, repo: PreparedRepo):
    await repo_read_client.assert_get(
        f"/repos/{repo.id}",
        expected_status_code=200,
        expected_json=repo.expected_api_response({"stats": None}),
    )


async def test_repo_get_with_all_fields(
    superadmin_client: HttpTestHelper,
    log_i18n_profile: PreparedLogI18nProfile,
    repo_builder: RepoBuilder,
):
    repo = await repo_builder(
        {
            "log_i18n_profile_id": log_i18n_profile.id,
            "retention_period": 30,
            "status": "readonly",
        }
    )

    await superadmin_client.assert_get(
        f"/repos/{repo.id}",
        expected_status_code=200,
        expected_json=repo.expected_api_response({"stats": None}),
    )


async def test_repo_get_with_stats_empty(
    repo_read_client: HttpTestHelper, repo: PreparedRepo
):
    await repo_read_client.assert_get(
        f"/repos/{repo.id}?include=stats",
        expected_status_code=200,
        expected_json=repo.expected_api_response(
            {
                "stats": {
                    "last_log_date": None,
                    "log_count": 0,
                    "storage_size": matchers.IsA(int),
                }
            }
        ),
    )


async def test_repo_get_with_stats(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log(
        superadmin_client, emitted_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    await repo.create_log(
        superadmin_client, emitted_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await superadmin_client.assert_get(
        f"/repos/{repo.id}?include=stats",
        expected_status_code=200,
        expected_json=repo.expected_api_response(
            {
                "stats": {
                    "last_log_date": "2024-01-02T00:00:00.000Z",
                    "log_count": 2,
                    "storage_size": matchers.IsA(int),
                }
            }
        ),
    )


async def test_repo_get_with_stats_disabled_repo(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.update_status(superadmin_client, "disabled")
    await superadmin_client.assert_get_ok(f"/repos/{repo.id}?include=stats")


async def test_repo_get_unknown_id(repo_read_client: HttpTestHelper):
    await repo_read_client.assert_get_not_found(f"/repos/{UNKNOWN_UUID}")


async def test_repo_get_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}")


async def test_repo_get_translation_for_user_not_configured(
    user_builder: UserBuilder, repo: PreparedRepo
):
    user = await user_builder(
        {"logs": {"repos": [{"repo_id": repo.id, "readable_entities": ["entity_A"]}]}}
    )

    async with user.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            f"/repos/{repo.id}/translation",
            expected_json=PreparedLogI18nProfile.EMPTY_TRANSLATION,
        )


async def test_repo_get_translation_for_user_not_available_for_user_lang(
    user_builder: UserBuilder,
    repo_builder: RepoBuilder,
):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18",
            "translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATION},
        },
    )
    repo = await repo_builder({"log_i18n_profile_id": profile.id})
    user = await user_builder({"logs": {"read": True}}, lang="fr")

    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get_ok(
            f"/repos/{repo.id}/translation",
            expected_json=PreparedLogI18nProfile.EMPTY_TRANSLATION,
        )


async def test_repo_get_translation_for_user_available_for_user_lang(
    user_builder: UserBuilder, repo_builder: RepoBuilder
):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18",
            "translations": {"fr": PreparedLogI18nProfile.FRENCH_TRANSLATION},
        },
    )
    repo = await repo_builder({"log_i18n_profile_id": profile.id})
    user = await user_builder({"logs": {"read": True}}, lang="fr")

    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get_ok(
            f"/repos/{repo.id}/translation",
            expected_json=PreparedLogI18nProfile.FRENCH_TRANSLATION,
        )


async def test_repo_get_translation_for_user_unknown_id(
    log_read_user_client: HttpTestHelper,
):
    await log_read_user_client.assert_get_not_found(
        f"/repos/{UNKNOWN_UUID}/translation"
    )


async def test_repo_get_translation_for_user_forbidden(
    user_builder: UserBuilder, repo: PreparedRepo
):
    user = await user_builder({})  # a user without permissions
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get_forbidden(f"/repos/{repo.id}/translation")


async def test_repo_get_translation_for_user_as_apikey(
    apikey_builder: ApikeyBuilder, repo: PreparedRepo
):
    apikey = await apikey_builder({"is_superadmin": True})
    async with apikey.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get_forbidden(f"/repos/{repo.id}/translation")


async def test_repo_get_translation_not_configured(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get_ok(
        f"/repos/{repo.id}/translations/fr",
        expected_json=PreparedLogI18nProfile.EMPTY_TRANSLATION,
    )


async def test_repo_get_translation_not_available_for_lang(
    log_read_client: HttpTestHelper, repo_builder: RepoBuilder
):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18",
            "translations": {"en": PreparedLogI18nProfile.ENGLISH_TRANSLATION},
        },
    )
    repo = await repo_builder({"log_i18n_profile_id": profile.id})
    await log_read_client.assert_get_ok(
        f"/repos/{repo.id}/translations/fr",
        expected_json=PreparedLogI18nProfile.EMPTY_TRANSLATION,
    )


async def test_repo_get_translation_for_user_available_for_lang(
    log_read_client: HttpTestHelper,
    repo_builder: RepoBuilder,
):
    profile = await PreparedLogI18nProfile.create(
        {
            "name": "i18",
            "translations": {"fr": PreparedLogI18nProfile.FRENCH_TRANSLATION},
        },
    )
    repo = await repo_builder({"log_i18n_profile_id": profile.id})

    await log_read_client.assert_get_ok(
        f"/repos/{repo.id}/translations/fr",
        expected_json=PreparedLogI18nProfile.FRENCH_TRANSLATION,
    )


async def test_repo_get_translation_unknown_id(log_read_user_client: HttpTestHelper):
    await log_read_user_client.assert_get_not_found(
        f"/repos/{UNKNOWN_UUID}/translations/en"
    )


async def test_repo_get_translation_unknown_lang(
    log_read_user_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_user_client.assert_get_bad_request(
        f"/repos/{repo.id}/translations/it"
    )


async def test_repo_get_translation_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(f"/repos/{repo.id}/translations/fr")


async def test_repo_get_translation_template_empty(
    repo_read_client: HttpTestHelper, repo: PreparedRepo
):
    await repo_read_client.assert_get_ok(
        f"/repos/{repo.id}/translations/template",
        expected_json=PreparedLogI18nProfile.EMPTY_TRANSLATION,
    )


async def test_repo_get_translation_template(
    superadmin_client: HttpTestHelper,
    repo_read_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await repo.create_log(
        superadmin_client,
        {
            "action": {
                "type": "user_login",
                "category": "authentication",
            },
            "entity_path": [{"ref": "entity", "name": "Entity"}],
            "source": [
                {"name": "ip", "value": "1.1.1.1"},
                {"name": "user_agent", "value": "Mozilla/5.0"},
                {"name": "enum_key", "value": "enum_value", "type": "enum"},
            ],
            "actor": {
                "type": "user",
                "ref": "user:123",
                "name": "User 123",
                "extra": [
                    {"name": "role", "value": "admin"},
                    {"name": "enum_key", "value": "enum_value", "type": "enum"},
                ],
            },
            "resource": {
                "ref": "core",
                "type": "module",
                "name": "Core Module",
                "extra": [
                    {"name": "creator", "value": "xyz"},
                    {"name": "enum_key", "value": "enum_value", "type": "enum"},
                ],
            },
            "details": [
                {"name": "some_key", "value": "some_value"},
                {"name": "other_key", "value": "other_value"},
                {"name": "enum_key", "value": "enum_value", "type": "enum"},
            ],
            "tags": [
                {
                    "type": "simple_tag",
                },
                {"ref": "rich_tag:1", "type": "rich_tag", "name": "Rich tag"},
            ],
        },
    )

    await repo_read_client.assert_get_ok(
        f"/repos/{repo.id}/translations/template",
        expected_json={
            "action_type": {
                "user_login": "",
            },
            "action_category": {
                "authentication": "",
            },
            "actor_type": {
                "user": "",
            },
            "actor_extra_field_name": {
                "role": "",
                "enum_key": "",
            },
            "actor_extra_field_value_enum": {
                "enum_key": {
                    "enum_value": "",
                },
            },
            "detail_field_name": {
                "some_key": "",
                "other_key": "",
                "enum_key": "",
            },
            "detail_field_value_enum": {
                "enum_key": {
                    "enum_value": "",
                },
            },
            "resource_extra_field_name": {
                "creator": "",
                "enum_key": "",
            },
            "resource_extra_field_value_enum": {
                "enum_key": {
                    "enum_value": "",
                },
            },
            "resource_type": {
                "module": "",
            },
            "source_field_name": {
                "ip": "",
                "user_agent": "",
                "enum_key": "",
            },
            "source_field_value_enum": {
                "enum_key": {
                    "enum_value": "",
                },
            },
            "tag_type": {
                "simple_tag": "",
                "rich_tag": "",
            },
            "attachment_type": {},
        },
    )


async def test_repo_get_translation_template_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_get_forbidden(
        f"/repos/{repo.id}/translations/template"
    )


async def test_repo_get_translation_template_unknown_id(
    repo_read_client: HttpTestHelper,
):
    await repo_read_client.assert_get_not_found(
        f"/repos/{UNKNOWN_UUID}/translations/template"
    )


async def test_repo_list(repo_read_client: HttpTestHelper, repo_builder: RepoBuilder):
    repos = [await repo_builder({}) for _ in range(5)]

    await do_test_page_pagination_common_scenarios(
        repo_read_client,
        "/repos",
        [
            repo.expected_api_response({"stats": None})
            for repo in sorted(repos, key=lambda r: r.data["name"])
        ],
    )


async def test_repo_list_with_search(
    repo_read_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repos = [await repo_builder({"name": f"repo_{i}"}) for i in range(2)]

    await repo_read_client.assert_get_ok(
        "/repos?q=repo_1",
        expected_json={
            "items": [repos[1].expected_api_response({"stats": None})],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_repo_list_with_stats(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log(
        superadmin_client,
        emitted_at=datetime.fromisoformat("2024-01-01T00:00:00.123Z"),
    )

    await superadmin_client.assert_get(
        f"/repos?include=stats",
        expected_status_code=200,
        expected_json={
            "items": [
                repo.expected_api_response(
                    {
                        "stats": {
                            "last_log_date": "2024-01-01T00:00:00.123Z",
                            "log_count": 1,
                            "storage_size": matchers.IsA(int),
                        }
                    }
                )
            ],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_repo_list_all_statuses(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repos = []
    for i, status in enumerate(("enabled", "readonly", "disabled")):
        repo = await repo_builder({"name": f"repo_{i}", "status": status})
        repos.append(repo)

    await superadmin_client.assert_get_ok(
        "/repos",
        expected_json={
            "items": [repo.expected_api_response({"stats": None}) for repo in repos],
            "pagination": {"page": 1, "page_size": 10, "total": 3, "total_pages": 1},
        },
    )


async def test_repo_list_forbidden(no_permission_client: HttpTestHelper):
    await no_permission_client.assert_get_forbidden("/repos")


async def test_repo_list_user_repos_simple(
    user_builder: UserBuilder, repo: PreparedRepo
):
    # some very basic test to ensure that the response is properly shaped
    # we'll test the permissions in a separate test

    user = await user_builder({"is_superadmin": True})

    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await client.assert_get_ok(
            "/users/me/repos",
            expected_json={
                "items": [
                    strip_dict_keys(
                        repo.expected_api_response(
                            {
                                "permissions": {
                                    "read": True,
                                    "write": True,
                                    "readable_entities": [],
                                }
                            }
                        ),
                        "status",
                        "created_at",
                        "updated_at",
                        "retention_period",
                        "stats",
                        "log_i18n_profile_id",
                    )
                ],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 1,
                    "total_pages": 1,
                },
            },
        )


async def _test_repo_list_user_repos(
    client: HttpTestHelper, params: dict, expected: dict[str, dict]
):
    resp = await client.assert_get_ok(
        "/users/me/repos",
        params=params,
    )
    items = resp.json()["items"]
    assert len(items) == len(expected)
    for expected_repo, expected_repo_perms in expected.items():
        ic(expected_repo, expected_repo_perms)
        assert any(
            repo["id"] == expected_repo and repo["permissions"] == expected_repo_perms
            for repo in items
        )


async def test_repo_list_user_repos_with_permissions(
    user_builder: UserBuilder, repo_builder: RepoBuilder
):
    repo_1 = await repo_builder({"name": "repo_1"})
    repo_2 = await repo_builder({"name": "repo_2"})
    repo_3 = await repo_builder({"name": "repo_3"})
    repo_readonly = await repo_builder({"name": "repo_readonly", "status": "readonly"})
    repo_disabled = await repo_builder({"name": "repo_disabled", "status": "disabled"})

    # Test #1 with user having read&write permissions on all repos
    user = await user_builder({"logs": {"read": True, "write": True}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {
                repo_1.id: {
                    "read": True,
                    "write": True,
                    "readable_entities": [],
                },
                repo_2.id: {
                    "read": True,
                    "write": True,
                    "readable_entities": [],
                },
                repo_3.id: {
                    "read": True,
                    "write": True,
                    "readable_entities": [],
                },
                repo_readonly.id: {
                    "read": True,
                    "write": False,
                    "readable_entities": [],
                },
            },
        )

    # Test #2 with user having specific permissions on various repos
    user = await user_builder(
        {
            "logs": {
                "repos": [
                    {"repo_id": repo_1.id, "read": True, "write": False},
                    {"repo_id": repo_2.id, "read": False, "write": True},
                    {
                        "repo_id": repo_3.id,
                        "read": False,
                        "write": True,
                        "readable_entities": ["entity1"],
                    },
                    {"repo_id": repo_readonly.id, "read": True, "write": True},
                    {"repo_id": repo_disabled.id, "read": True, "write": True},
                ]
            }
        }
    )
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {
                repo_1.id: {
                    "read": True,
                    "write": False,
                    "readable_entities": [],
                },
                repo_2.id: {
                    "read": False,
                    "write": True,
                    "readable_entities": [],
                },
                repo_3.id: {
                    "read": False,
                    "write": True,
                    "readable_entities": ["entity1"],
                },
                repo_readonly.id: {
                    "read": True,
                    "write": False,
                    "readable_entities": [],
                },
            },
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True},
            {
                repo_1.id: {
                    "read": True,
                    "write": False,
                    "readable_entities": [],
                },
                repo_3.id: {
                    "read": False,
                    "write": True,
                    "readable_entities": ["entity1"],
                },
                repo_readonly.id: {
                    "read": True,
                    "write": False,
                    "readable_entities": [],
                },
            },
        )
        await _test_repo_list_user_repos(
            client,
            {"has_write_permission": True},
            {
                repo_2.id: {
                    "read": False,
                    "write": True,
                    "readable_entities": [],
                },
                repo_3.id: {
                    "read": False,
                    "write": True,
                    "readable_entities": ["entity1"],
                },
            },
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True, "has_write_permission": True},
            {
                repo_3.id: {
                    "read": False,
                    "write": True,
                    "readable_entities": ["entity1"],
                }
            },
        )

    # Test #3 with user having no log permissions (but can manage repos)
    user = await user_builder({"management": {"repos": {"read": True, "write": True}}})
    async with user.client() as client:
        client: HttpTestHelper  # make pycharm happy
        await _test_repo_list_user_repos(
            client,
            {},
            {},  # no repo should be returned
        )
        await _test_repo_list_user_repos(
            client,
            {"has_read_permission": True},
            {},  # no repo should be returned
        )


async def test_repo_list_user_repos_unauthorized(anon_client: HttpTestHelper):
    # /users/me/repos does not require any permission (as its job is to
    # return authorized repos for log access)
    # but the user must be authenticated
    await anon_client.assert_get_unauthorized("/users/me/repos")


async def test_repo_list_user_repos_as_apikey(apikey_builder: ApikeyBuilder):
    apikey = await apikey_builder({"is_superadmin": True})
    async with apikey.client() as client:
        await client.assert_get_forbidden("/users/me/repos")


async def test_repo_delete(repo_write_client: HttpTestHelper, superadmin_client):
    resp = await repo_write_client.assert_post_created("/repos", json={"name": "repo"})
    repo_id = resp.json()["id"]
    await repo_write_client.assert_delete_no_content(f"/repos/{repo_id}")
    await superadmin_client.assert_get_not_found(f"/repos/{repo_id}")


async def test_repo_delete_with_related_resources(
    user_builder: UserBuilder, repo: PreparedRepo
):
    remaining_repo = repo  # repo that will not be deleted
    superadmin = await user_builder({"is_superadmin": True})

    async with superadmin.client() as client:
        client: HttpTestHelper  # make pycharm happy

        resp = await client.assert_post_created("/repos", json={"name": "repo"})
        to_be_deleted_repo_id = resp.json()["id"]

        # Create an API key with permissions on the to_be_deleted_repo + another repo
        apikey = await PreparedApikey.create(
            client,
            {
                "name": "apikey",
                "permissions": {
                    "logs": {
                        "repos": [
                            {"repo_id": to_be_deleted_repo_id, "read": True},
                            {"repo_id": remaining_repo.id, "read": True},
                        ]
                    }
                },
            },
        )

        # Create a user with permissions on the to_be_deleted_repo + another repo
        user = await PreparedUser.create(
            client,
            PreparedUser.prepare_data(
                {
                    "permissions": {
                        "logs": {
                            "repos": [
                                {"repo_id": to_be_deleted_repo_id, "read": True},
                                {"repo_id": remaining_repo.id, "read": True},
                            ]
                        }
                    },
                }
            ),
        )

        # Create a log filter with the to_be_deleted_repo and another filter with another repo
        await superadmin.create_log_filter(
            {
                "name": "filter_to_be_deleted",
                "repo_id": to_be_deleted_repo_id,
                "search_params": {},
                "columns": [],
            }
        )
        log_filter = await superadmin.create_log_filter(
            {
                "name": "filter_to_keep",
                "repo_id": remaining_repo.id,
                "search_params": {},
                "columns": [],
            },
        )

        # Delete the repo
        await client.assert_delete_no_content(f"/repos/{to_be_deleted_repo_id}")

    ###
    # Check that the related resources have been deleted
    ###

    async with superadmin.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            f"/apikeys/{apikey.id}",
            expected_json=apikey.expected_api_response(
                {
                    "permissions": {
                        **DEFAULT_PERMISSIONS,
                        "logs": {
                            "read": False,
                            "write": False,
                            "repos": [
                                {
                                    "repo_id": remaining_repo.id,
                                    "read": True,
                                    "write": False,
                                    "readable_entities": [],
                                }
                            ],
                        },
                    }
                }
            ),
        )

    async with superadmin.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            f"/users/{user.id}",
            expected_json=user.expected_api_response(
                {
                    "permissions": {
                        **DEFAULT_PERMISSIONS,
                        "logs": {
                            "read": False,
                            "write": False,
                            "repos": [
                                {
                                    "repo_id": remaining_repo.id,
                                    "read": True,
                                    "write": False,
                                    "readable_entities": [],
                                }
                            ],
                        },
                    }
                }
            ),
        )

    async with superadmin.client() as client:
        client: HttpTestHelper
        await client.assert_get_ok(
            f"/users/me/logs/filters",
            expected_json={
                "items": [log_filter.expected_api_response()],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 1,
                    "total_pages": 1,
                },
            },
        )


async def test_repo_delete_unknown_id(repo_write_client: HttpTestHelper):
    await repo_write_client.assert_delete_not_found(f"/repos/{UNKNOWN_UUID}")


async def test_repo_delete_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_delete_forbidden(f"/repos/{repo.id}")
