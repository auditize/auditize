from copy import deepcopy

from icecream import ic
import pytest

from auditize.permissions.assertions import can_read_logs
from auditize.permissions.models import Permissions
from auditize.permissions.operations import normalize_permissions, authorize_grant, update_permissions, authorize_access, get_applicable_permissions
from auditize.common.exceptions import PermissionDenied


def _test_access_perms_normalization(input: dict, expected: dict):
    input = Permissions.model_validate(input)

    assert normalize_permissions(input).model_dump() == expected


def test_normalization_superadmin_only():
    _test_access_perms_normalization(
        {"is_superadmin": True},
        {
            "is_superadmin": True,
            "logs": {
                "read": False,
                "write": False,
                "repos": {},
            },
            "entities": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def test_normalization_superadmin_with_explicit_permissions():
    _test_access_perms_normalization(
        {
            "is_superadmin": True,
            "entities": {
                "repos": {"read": True},
                "users": {"write": True},
                "integrations": {"read": True, "write": True},
            },
            "logs": {
                "read": True,
                "write": True,
                "repos": {
                    "repo1": {"read": True, "write": True},
                    "repo2": {"read": True, "write": True},
                },
            },
        },
        {
            "is_superadmin": True,
            "entities": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
            "logs": {
                "read": False,
                "write": False,
                "repos": {},
            },
        },
    )


def test_normalization_superadmin_with_log_permissions():
    _test_access_perms_normalization(
        {
            "is_superadmin": True,
            "logs": {
                "read": True,
                "write": True,
                "repos": {
                    "repo1": {"read": True, "write": True},
                    "repo2": {"read": True, "write": True},
                },
            },
        },
        {
            "is_superadmin": True,
            "logs": {
                "read": False,
                "write": False,
                "repos": {},
            },
            "entities": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def test_normalization_read_logs_on_all_repos():
    _test_access_perms_normalization(
        {
            "logs": {
                "read": True,
                "write": False,
                "repos": {
                    "repo1": {"read": True, "write": True},
                    "repo2": {"read": False, "write": True},
                    "repo3": {"read": True, "write": False},
                },
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": False,
                "repos": {
                    "repo1": {"read": False, "write": True},
                    "repo2": {"read": False, "write": True}
                },
            },
            "entities": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def test_normalization_write_logs_on_all_repos():
    _test_access_perms_normalization(
        {
            "logs": {
                "read": False,
                "write": True,
                "repos": {
                    "repo1": {"read": True, "write": True},
                    "repo2": {"read": False, "write": True},
                    "repo3": {"read": True, "write": False},
                },
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": True,
                "repos": {
                    "repo1": {"read": True, "write": False},
                    "repo3": {"read": True, "write": False},
                },
            },
            "entities": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def test_normalization_read_and_write_logs_on_all_repos():
    _test_access_perms_normalization(
        {
            "logs": {
                "read": True,
                "write": True,
                "repos": {
                    "repo1": {"read": True, "write": True},
                    "repo2": {"read": False, "write": True},
                    "repo3": {"read": True, "write": False},
                },
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": True,
                "repos": {},
            },
            "entities": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def assert_authorized(perms, *grants):
    perms = Permissions.model_validate(perms)

    for grant in grants:
        ic(grant)
        authorize_grant(perms, Permissions.model_validate(grant))


def assert_unauthorized(perms, *grants):
    perms = Permissions.model_validate(perms)

    for grant in grants:
        ic(grant)
        with pytest.raises(PermissionDenied):
            authorize_grant(perms, Permissions.model_validate(grant))


def test_authorize_grant_as_superadmin():
    assert_authorized(
        {"is_superadmin": True},
        ###
        {"is_superadmin": True},
        {"is_superadmin": False},
        {"logs": {"read": True, "write": True}},
        {"logs": {"read": False, "write": False}},
        {"logs": {"repos": {"repo1": {"read": True, "write": True}}}},
        {"logs": {"repos": {"repo1": {"read": False, "write": False}}}},
        {"entities": {"repos": {"read": True, "write": True}}},
        {"entities": {"repos": {"read": False, "write": False}}},
        {"entities": {"users": {"read": True, "write": True}}},
        {"entities": {"users": {"read": False, "write": False}}},
        {"entities": {"integrations": {"read": True, "write": True}}},
        {"entities": {"integrations": {"read": False, "write": False}}},
    )


def test_authorize_grant_as_no_right():
    assert_unauthorized(
        {},
        ###
        {"is_superadmin": True},
        {"is_superadmin": False},
        {"logs": {"read": True, "write": True}},
        {"logs": {"read": False, "write": False}},
        {"logs": {"repos": {"repo1": {"read": True, "write": True}}}},
        {"logs": {"repos": {"repo1": {"read": False, "write": False}}}},
        {"entities": {"repos": {"read": True, "write": True}}},
        {"entities": {"repos": {"read": False, "write": False}}},
        {"entities": {"users": {"read": True, "write": True}}},
        {"entities": {"users": {"read": False, "write": False}}},
        {"entities": {"integrations": {"read": True, "write": True}}},
        {"entities": {"integrations": {"read": False, "write": False}}},
    )


def test_authorize_grant_on_logs_as_permissions_on_all_repos():
    read_perms = {"logs": {"read": True}}
    assert_authorized(read_perms, {"logs": {"read": True}})
    assert_unauthorized(read_perms, {"logs": {"write": True}})

    write_perms = {"logs": {"write": True}}
    assert_authorized(write_perms, {"logs": {"write": True}})
    assert_unauthorized(write_perms, {"logs": {"read": True}})


def test_permission_assertions_on_logs_as_permissions_specific_repos():
    perms = {
        "logs": {
            "repos": {
                "repo1": {"read": True, "write": False},
                "repo2": {"read": False, "write": True},
            }
        }
    }
    assert_authorized(
        perms,
        ###
        {"logs": {"repos": {"repo1": {"read": True}}}},
        {"logs": {"repos": {"repo2": {"write": True}}}},
    )
    assert_unauthorized(
        perms,
        ###
        {"logs": {"repos": {"repo1": {"write": True}}}},
        {"logs": {"repos": {"repo2": {"read": True}}}},
    )


def test_permission_assertions_on_entities_as_specific_permissions():
    every_possible_entities_perms = {
        "entities": {
            "repos": {"read": True, "write": True},
            "users": {"read": True, "write": True},
            "integrations": {"read": True, "write": True},
        }
    }
    for entity_type in "repos", "users", "integrations":
        for perm_type in "read", "write":
            target_perms = {
                "entities": {entity_type: {perm_type: True}}
            }

            # test authorized with the minimum permissions
            assert_authorized(target_perms, target_perms)

            # test unauthorized with all permissions on entities but not the requested one
            all_perms_but = deepcopy(every_possible_entities_perms)
            all_perms_but["entities"][entity_type][perm_type] = False
            assert_unauthorized(all_perms_but, target_perms)


def _test_update_permission(orig: dict, update: dict, expected: dict):
    orig = Permissions.model_validate(orig)
    update = Permissions.model_validate(update)

    actual = update_permissions(orig, update)
    assert actual.model_dump() == expected


def test_update_permission_grant_superadmin():
    _test_update_permission(
        {
            "logs": {
                "read": True,
                "write": False,
                "repos": {
                    "repo1": {"write": True},
                },
            },
            "entities": {"repos": {"read": True, "write": True}}
        },
        {"is_superadmin": True},
        {
            "is_superadmin": True,
            "logs": {
                "read": False,
                "write": False,
                "repos": {},
            },
            "entities": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def test_update_permission_grant_individual_permissions():
    _test_update_permission(
        {
            "logs": {
                "read": True,
                "write": False,
                "repos": {
                    "repo1": {"write": True},
                },
            },
            "entities": {"repos": {"read": True, "write": True}}
        },
        {
            "logs": {"write": True},
            "entities": {"users": {"read": True}},
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": True,
                "repos": {},
            },
            "entities": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def test_update_permission_drop_individual_permissions():
    _test_update_permission(
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": True,
                "repos": {},
            },
            "entities": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
        {
            "logs": {
                "write": False,
                "repos": {
                    "repo1": {"write": True},
                },
            },
            "entities": {"users": {"read": False}},
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": False,
                "repos": {
                    "repo1": {"read": False, "write": True},
                },
            },
            "entities": {
                "repos": {"read": True, "write": True},
                "users": {"read": False, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def _test_get_applicable_permissions(input: dict, expected: dict):
    input = Permissions.model_validate(input)
    assert get_applicable_permissions(input).model_dump() == expected


def test_get_applicable_permissions_superadmin():
    _test_get_applicable_permissions(
        {"is_superadmin": True},
        {
            "is_superadmin": True,
            "logs": {"read": True, "write": True},
            "entities": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": True},
                "integrations": {"read": True, "write": True},
            },
        },
    )


def test_get_applicable_permissions_partial_rights():
    _test_get_applicable_permissions(
        {
            "logs": {
                "read": True,
                "write": False,
                "repos": {
                    "repo1": {"read": True, "write": False},
                    "repo2": {"read": False, "write": True},
                },
            },
            "entities": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
        {
            "is_superadmin": False,
            "logs": {"read": True, "write": False},
            "entities": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "integrations": {"read": False, "write": False},
            },
        },
    )


def test_authorize_access():
    assertion = can_read_logs("repo1")

    # OK case
    authorize_access(Permissions(is_superadmin=True), assertion)

    # Not OK case
    with pytest.raises(PermissionDenied, match="Access denied"):
        authorize_access(Permissions(), assertion)
