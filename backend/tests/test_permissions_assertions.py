from copy import deepcopy

from icecream import ic

from auditize.permissions.models import Permissions
from auditize.permissions.assertions import (
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
)


def assert_permission(perms, assertions, result):
    if type(assertions) not in (list, tuple):
        assertions = [assertions]
    for assertion in assertions:
        ic(assertion)
        assert assertion(Permissions.model_validate(perms)) is result


def assert_authorized(perms, *assertions):
    assert_permission(perms, assertions, True)


def assert_unauthorized(perms, *assertions):
    assert_permission(perms, assertions, False)


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
    read_perms = {"logs": {"read": True}}
    assert_authorized(read_perms, can_read_logs("repo1"))
    assert_authorized(read_perms, can_read_logs())
    assert_unauthorized(read_perms, can_write_logs("repo1"))
    assert_unauthorized(read_perms, can_write_logs())

    write_perms = {"logs": {"write": True}}
    assert_authorized(write_perms, can_write_logs("repo1"))
    assert_authorized(write_perms, can_write_logs())
    assert_unauthorized(write_perms, can_read_logs("repo1"))
    assert_unauthorized(write_perms, can_read_logs())


def test_permission_assertions_on_logs_as_permissions_specific_repos():
    perms = {
        "logs": {
            "repos": {
                "repo1": {"read": True, "write": False},
                "repo2": {"read": False, "write": True},
            }
        }
    }
    assert_authorized(perms, can_read_logs("repo1"), can_write_logs("repo2"))
    assert_unauthorized(perms, can_write_logs("repo1"), can_read_logs("repo2"))


def test_permission_assertions_on_entities_as_specific_permissions():
    every_possible_entities_perms = {
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
            # test authorized with the minimum permissions
            no_perms_but = {
                "entities": {entity_type: {perm_type: True}}
            }
            assert_authorized(no_perms_but, permission_assertions[entity_type][perm_type])

            # test unauthorized with all permissions on entities but not the requested one
            all_perms_but = deepcopy(every_possible_entities_perms)
            all_perms_but["entities"][entity_type][perm_type] = False
            assert_unauthorized(all_perms_but, permission_assertions[entity_type][perm_type])


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
