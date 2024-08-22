from copy import deepcopy
from uuid import UUID

import pytest
from icecream import ic

from auditize.exceptions import PermissionDenied
from auditize.permissions.assertions import can_read_logs
from auditize.permissions.models import Permissions
from auditize.permissions.operations import (
    authorize_access,
    authorize_grant,
    compute_applicable_permissions,
    normalize_permissions,
    update_permissions,
)

REPO_1 = UUID("8276de01-c6f2-4174-bbbf-cadb8e9832e6")
REPO_2 = UUID("4b3a4f91-8131-4d06-8edb-7d9d1353217b")
REPO_3 = UUID("14f27afe-902d-4176-8612-920bc59f95cb")
REPO_4 = UUID("8ecdf2db-c70d-4cad-8610-d4334e65d0df")


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
                "repos": [],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_normalization_superadmin_with_explicit_permissions():
    _test_access_perms_normalization(
        {
            "is_superadmin": True,
            "management": {
                "repos": {"read": True},
                "users": {"write": True},
                "apikeys": {"read": True, "write": True},
            },
            "logs": {
                "read": True,
                "write": True,
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": True},
                    {"repo_id": REPO_2, "read": True, "write": True},
                ],
            },
        },
        {
            "is_superadmin": True,
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
            "logs": {
                "read": False,
                "write": False,
                "repos": [],
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
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": True},
                    {"repo_id": REPO_2, "read": True, "write": True},
                ],
            },
        },
        {
            "is_superadmin": True,
            "logs": {
                "read": False,
                "write": False,
                "repos": [],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_normalization_read_logs_on_all_repos():
    _test_access_perms_normalization(
        {
            "logs": {
                "read": True,
                "write": False,
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": True},
                    {"repo_id": REPO_2, "read": False, "write": True},
                    {"repo_id": REPO_3, "read": True, "write": False},
                    {
                        "repo_id": REPO_4,
                        "read": True,
                        "write": True,
                        "readable_entities": ["entity1", "entity2"],
                    },
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": False,
                        "write": True,
                        "readable_entities": [],
                    },
                    {
                        "repo_id": REPO_2,
                        "read": False,
                        "write": True,
                        "readable_entities": [],
                    },
                    {
                        "repo_id": REPO_4,
                        "read": False,
                        "write": True,
                        "readable_entities": [],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_normalization_repo_entities_without_read_permission():
    _test_access_perms_normalization(
        {
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": False,
                        "write": True,
                        "readable_entities": ["entity1", "entity2"],
                    },
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": False,
                        "write": True,
                        "readable_entities": [],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_normalization_write_logs_on_all_repos():
    _test_access_perms_normalization(
        {
            "logs": {
                "read": False,
                "write": True,
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": True},
                    {"repo_id": REPO_2, "read": False, "write": True},
                    {"repo_id": REPO_3, "read": True, "write": False},
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": True,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": True,
                        "write": False,
                        "readable_entities": [],
                    },
                    {
                        "repo_id": REPO_3,
                        "read": True,
                        "write": False,
                        "readable_entities": [],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_normalization_read_and_write_logs_on_all_repos():
    _test_access_perms_normalization(
        {
            "logs": {
                "read": True,
                "write": True,
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": True},
                    {"repo_id": REPO_2, "read": False, "write": True},
                    {"repo_id": REPO_3, "read": True, "write": False},
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": True,
                "repos": [],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
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
        {"logs": {"repos": [{"repo_id": REPO_1, "read": True, "write": True}]}},
        {"logs": {"repos": [{"repo_id": REPO_1, "read": False, "write": False}]}},
        {"management": {"repos": {"read": True, "write": True}}},
        {"management": {"repos": {"read": False, "write": False}}},
        {"management": {"users": {"read": True, "write": True}}},
        {"management": {"users": {"read": False, "write": False}}},
        {"management": {"apikeys": {"read": True, "write": True}}},
        {"management": {"apikeys": {"read": False, "write": False}}},
    )


def test_authorize_grant_as_no_right():
    assert_unauthorized(
        {},
        ###
        {"is_superadmin": True},
        {"is_superadmin": False},
        {"logs": {"read": True, "write": True}},
        {"logs": {"read": False, "write": False}},
        {"logs": {"repos": [{"repo_id": REPO_1, "read": True, "write": True}]}},
        {"logs": {"repos": [{"repo_id": REPO_1, "read": False, "write": False}]}},
        {"management": {"repos": {"read": True, "write": True}}},
        {"management": {"repos": {"read": False, "write": False}}},
        {"management": {"users": {"read": True, "write": True}}},
        {"management": {"users": {"read": False, "write": False}}},
        {"management": {"apikeys": {"read": True, "write": True}}},
        {"management": {"apikeys": {"read": False, "write": False}}},
    )


def test_authorize_grant_on_logs_as_permissions_on_all_repos():
    read_perms = {"logs": {"read": True}}
    assert_authorized(read_perms, {"logs": {"read": True}})
    assert_unauthorized(read_perms, {"logs": {"write": True}})

    write_perms = {"logs": {"write": True}}
    assert_authorized(write_perms, {"logs": {"write": True}})
    assert_unauthorized(write_perms, {"logs": {"read": True}})


def test_authorize_grant_on_logs_with_entity():
    granted_perms = {
        "logs": {
            "repos": [
                {"repo_id": REPO_1, "read": True, "readable_entities": ["entity1"]},
            ]
        }
    }

    assert_authorized(
        {"logs": {"repos": [{"repo_id": REPO_1, "read": True, "write": False}]}},
        granted_perms,
    )

    # the grantor must have full direct/indirect read permission on the repo
    # to grant access; grantors with read access limited to certain entities are
    # not allowed to grant permissions (even on the same entities):
    assert_unauthorized(granted_perms, granted_perms)


def test_permission_assertions_on_logs_as_permissions_specific_repos():
    perms = {
        "logs": {
            "repos": [
                {"repo_id": REPO_1, "read": True, "write": False},
                {"repo_id": REPO_2, "read": False, "write": True},
            ]
        }
    }
    assert_authorized(
        perms,
        ###
        {"logs": {"repos": [{"repo_id": REPO_1, "read": True}]}},
        {"logs": {"repos": [{"repo_id": REPO_2, "write": True}]}},
    )
    assert_unauthorized(
        perms,
        ###
        {"logs": {"repos": [{"repo_id": REPO_1, "write": True}]}},
        {"logs": {"repos": [{"repo_id": REPO_2, "read": True}]}},
    )


def test_permission_assertions_on_management_as_specific_permissions():
    every_possible_management_perms = {
        "management": {
            "repos": {"read": True, "write": True},
            "users": {"read": True, "write": True},
            "apikeys": {"read": True, "write": True},
        }
    }
    for entity_type in "repos", "users", "apikeys":
        for perm_type in "read", "write":
            target_perms = {"management": {entity_type: {perm_type: True}}}

            # test authorized with the minimum permissions
            assert_authorized(target_perms, target_perms)

            # test unauthorized with all permissions on management but not the requested one
            all_perms_but = deepcopy(every_possible_management_perms)
            all_perms_but["management"][entity_type][perm_type] = False
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
                "repos": [
                    {"repo_id": REPO_1, "write": True},
                ],
            },
            "management": {"repos": {"read": True, "write": True}},
        },
        {"is_superadmin": True},
        {
            "is_superadmin": True,
            "logs": {
                "read": False,
                "write": False,
                "repos": [],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_update_permission_grant_individual_permissions():
    _test_update_permission(
        {
            "logs": {
                "read": True,
                "write": False,
                "repos": [
                    {"repo_id": REPO_1, "write": True},
                ],
            },
            "management": {"repos": {"read": True, "write": True}},
        },
        {
            "logs": {"write": True},
            "management": {"users": {"read": True}},
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": True,
                "repos": [],
            },
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "apikeys": {"read": False, "write": False},
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
                "repos": [],
            },
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
        {
            "logs": {
                "write": False,
                "repos": [
                    {"repo_id": REPO_1, "write": True},
                ],
            },
            "management": {"users": {"read": False}},
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": True,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": False,
                        "write": True,
                        "readable_entities": [],
                    },
                ],
            },
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_update_permission_grant_read_logs_on_entities_1():
    _test_update_permission(
        {},
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "read": True, "readable_entities": ["entity1"]},
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": True,
                        "write": False,
                        "readable_entities": ["entity1"],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_update_permission_grant_read_logs_on_entities_2():
    _test_update_permission(
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "read": True, "readable_entities": ["entity1"]},
                ],
            },
        },
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "read": True, "readable_entities": []},
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": True,
                        "write": False,
                        "readable_entities": [],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_update_permission_grant_read_logs_on_entities_3():
    _test_update_permission(
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "read": True, "readable_entities": ["entity1"]},
                ],
            },
        },
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "write": True},
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": True,
                        "write": True,
                        "readable_entities": ["entity1"],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_update_permissions_add_repo():
    _test_update_permission(
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": True},
                ],
            },
        },
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_2, "read": True, "write": True},
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_1,
                        "read": True,
                        "write": True,
                        "readable_entities": [],
                    },
                    {
                        "repo_id": REPO_2,
                        "read": True,
                        "write": True,
                        "readable_entities": [],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_update_permissions_drop_repo():
    _test_update_permission(
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": True},
                    {"repo_id": REPO_2, "read": True, "write": True},
                ],
            },
        },
        {
            "logs": {
                "repos": [
                    {"repo_id": REPO_1, "read": False, "write": False},
                ],
            },
        },
        {
            "is_superadmin": False,
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {
                        "repo_id": REPO_2,
                        "read": True,
                        "write": True,
                        "readable_entities": [],
                    },
                ],
            },
            "management": {
                "repos": {"read": False, "write": False},
                "users": {"read": False, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def _test_get_applicable_permissions(input: dict, expected: dict):
    input = Permissions.model_validate(input)
    assert compute_applicable_permissions(input).model_dump() == expected


def test_get_applicable_permissions_superadmin():
    _test_get_applicable_permissions(
        {"is_superadmin": True},
        {
            "is_superadmin": True,
            "logs": {"read": "all", "write": "all"},
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": True},
                "apikeys": {"read": True, "write": True},
            },
        },
    )


def test_get_applicable_permissions_partial_rights():
    _test_get_applicable_permissions(
        {
            "logs": {
                "read": False,
                "write": False,
                "repos": [
                    {"repo_id": REPO_1, "read": True, "write": False},
                    {"repo_id": REPO_2, "read": False, "write": True},
                    {
                        "repo_id": REPO_3,
                        "read": True,
                        "write": False,
                        "readable_entities": ["entity1"],
                    },
                ],
            },
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
        {
            "is_superadmin": False,
            "logs": {"read": "partial", "write": "partial"},
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_get_applicable_permissions_no_rights():
    _test_get_applicable_permissions(
        {
            "logs": {
                "read": False,
                "write": False,
            },
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
        {
            "is_superadmin": False,
            "logs": {"read": "none", "write": "none"},
            "management": {
                "repos": {"read": True, "write": True},
                "users": {"read": True, "write": False},
                "apikeys": {"read": False, "write": False},
            },
        },
    )


def test_authorize_access():
    assertion = can_read_logs(REPO_1)

    # OK case
    authorize_access(Permissions(is_superadmin=True), assertion)

    # Not OK case
    with pytest.raises(PermissionDenied):
        authorize_access(Permissions(), assertion)
