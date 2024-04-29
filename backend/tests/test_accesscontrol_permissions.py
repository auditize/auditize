from copy import deepcopy

import pytest
from icecream import ic

from auditize.accesscontrol.models import AccessRights
from auditize.accesscontrol.permissions import (
    can_read_logs,
    can_write_logs,
    can_read_repos,
    can_write_repos,
    can_read_users,
    can_write_users,
    can_read_integrations,
    can_write_integrations,
    permissions_or,
    permissions_and,
    authorize_access,
)
from auditize.common.exceptions import PermissionDenied


def assert_permission(rights, assertions, result):
    if type(assertions) not in (list, tuple):
        assertions = [assertions]
    for assertion in assertions:
        ic(assertion)
        assert assertion(AccessRights.model_validate(rights)) is result


def assert_authorized(rights, *assertions):
    assert_permission(rights, assertions, True)


def assert_unauthorized(rights, *assertions):
    assert_permission(rights, assertions, False)


def test_permission_assertions_as_superadmin():
    assert_authorized(
        {"is_superadmin": True},
        can_read_logs("repo1"),
        can_write_logs("repo2"),
        can_read_repos(),
        can_write_repos(),
        can_read_users(),
        can_write_users(),
        can_read_integrations(),
        can_write_integrations(),
    )


def test_permission_assertions_as_no_right():
    assert_unauthorized(
        {},
        can_read_logs("repo1"),
        can_write_logs("repo2"),
        can_read_repos(),
        can_write_repos(),
        can_read_users(),
        can_write_users(),
        can_read_integrations(),
        can_write_integrations(),
    )


def test_permission_assertions_on_logs_as_permissions_on_all_repos():
    read_rights = {"logs": {"read": True}}
    assert_authorized(read_rights, can_read_logs("repo1"))
    assert_unauthorized(read_rights, can_write_logs("repo1"))

    write_rights = {"logs": {"write": True}}
    assert_authorized(write_rights, can_write_logs("repo1"))
    assert_unauthorized(write_rights, can_read_logs("repo1"))


def test_permission_assertions_on_logs_as_permissions_specific_repos():
    rights = {
        "logs": {
            "repos": {
                "repo1": {"read": True, "write": False},
                "repo2": {"read": False, "write": True},
            }
        }
    }
    assert_authorized(rights, can_read_logs("repo1"), can_write_logs("repo2"))
    assert_unauthorized(rights, can_write_logs("repo1"), can_read_logs("repo2"))


def test_permission_assertions_on_entities_as_specific_permissions():
    every_possible_entities_rights = {
        "entities": {
            "repos": {"read": True, "write": True},
            "users": {"read": True, "write": True},
            "integrations": {"read": True, "write": True},
        }
    }
    permission_assertions = {
        "repos": {"read": can_read_repos(), "write": can_write_repos()},
        "users": {"read": can_read_users(), "write": can_write_users()},
        "integrations": {"read": can_read_integrations(), "write": can_write_integrations()},
    }
    for entity_type in "repos", "users", "integrations":
        for perm_type in "read", "write":
            # test authorized with the minimum rights
            no_rights_but = {
                "entities": {entity_type: {perm_type: True}}
            }
            assert_authorized(no_rights_but, permission_assertions[entity_type][perm_type])

            # test unauthorized with all rights on entities but not the requested one
            all_rights_but = deepcopy(every_possible_entities_rights)
            all_rights_but["entities"][entity_type][perm_type] = False
            assert_unauthorized(all_rights_but, permission_assertions[entity_type][perm_type])


def test_permissions_or():
    assertion = permissions_or(can_read_logs("repo1"), can_write_logs("repo1"))
    assert_authorized({"logs": {"read": True, "write": False}}, assertion)
    assert_authorized({"logs": {"read": False, "write": True}}, assertion)
    assert_unauthorized({}, assertion)


def test_permissions_and():
    assertion = permissions_and(can_read_logs("repo1"), can_write_logs("repo1"))
    assert_unauthorized({"logs": {"read": True, "write": False}}, assertion)
    assert_unauthorized({"logs": {"read": False, "write": True}}, assertion)
    assert_authorized({"logs": {"read": True, "write": True}}, assertion)


def test_authorize_access():
    assertion = can_read_logs("repo1")

    # OK case
    authorize_access(AccessRights(is_superadmin=True), assertion)

    # Not OK case
    with pytest.raises(PermissionDenied, match="Access denied"):
        authorize_access(AccessRights(), assertion)
