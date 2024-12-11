from copy import deepcopy
from uuid import UUID

from icecream import ic

from auditize.permissions.assertions import (
    can_read_apikey,
    can_read_logs_from_all_repos,
    can_read_logs_from_repo,
    can_read_repo,
    can_read_user,
    can_write_apikey,
    can_write_logs_to_all_repos,
    can_write_logs_to_repo,
    can_write_repo,
    can_write_user,
    permissions_and,
    permissions_or,
)
from auditize.permissions.models import Permissions

REPO_1 = UUID("8276de01-c6f2-4174-bbbf-cadb8e9832e6")
REPO_2 = UUID("4b3a4f91-8131-4d06-8edb-7d9d1353217b")


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
        can_read_logs_from_repo(REPO_1),
        can_write_logs_to_repo(REPO_2),
        can_read_repo(),
        can_write_repo(),
        can_read_user(),
        can_write_user(),
        can_read_apikey(),
        can_write_apikey(),
    )


def test_permission_assertions_as_no_right():
    assert_unauthorized(
        {},
        can_read_logs_from_repo(REPO_1),
        can_write_logs_to_repo(REPO_2),
        can_read_repo(),
        can_write_repo(),
        can_read_user(),
        can_write_user(),
        can_read_apikey(),
        can_write_apikey(),
    )


def test_permission_assertions_on_logs_as_permissions_on_all_repos():
    read_perms = {"logs": {"read": True}}
    assert_authorized(read_perms, can_read_logs_from_repo(REPO_1))
    assert_authorized(read_perms, can_read_logs_from_all_repos())
    assert_unauthorized(read_perms, can_write_logs_to_repo(REPO_1))
    assert_unauthorized(read_perms, can_write_logs_to_all_repos())

    write_perms = {"logs": {"write": True}}
    assert_authorized(write_perms, can_write_logs_to_repo(REPO_1))
    assert_authorized(write_perms, can_write_logs_to_all_repos())
    assert_unauthorized(write_perms, can_read_logs_from_repo(REPO_1))
    assert_unauthorized(write_perms, can_read_logs_from_all_repos())


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
        perms, can_read_logs_from_repo(REPO_1), can_write_logs_to_repo(REPO_2)
    )
    assert_unauthorized(
        perms, can_write_logs_to_repo(REPO_1), can_read_logs_from_repo(REPO_2)
    )


def test_permission_assertions_on_management_as_specific_permissions():
    every_possible_management_perms = {
        "management": {
            "repos": {"read": True, "write": True},
            "users": {"read": True, "write": True},
            "apikeys": {"read": True, "write": True},
        }
    }
    permission_assertions = {
        "repos": {"read": can_read_repo(), "write": can_write_repo()},
        "users": {"read": can_read_user(), "write": can_write_user()},
        "apikeys": {
            "read": can_read_apikey(),
            "write": can_write_apikey(),
        },
    }
    for entity_type in "repos", "users", "apikeys":
        for perm_type in "read", "write":
            # test authorized with the minimum permissions
            no_perms_but = {"management": {entity_type: {perm_type: True}}}
            assert_authorized(
                no_perms_but, permission_assertions[entity_type][perm_type]
            )

            # test unauthorized with all permissions on management but not the requested one
            all_perms_but = deepcopy(every_possible_management_perms)
            all_perms_but["management"][entity_type][perm_type] = False
            assert_unauthorized(
                all_perms_but, permission_assertions[entity_type][perm_type]
            )


def test_permissions_or():
    assertion = permissions_or(
        can_read_logs_from_repo(REPO_1), can_write_logs_to_repo(REPO_1)
    )
    assert_authorized({"logs": {"read": True, "write": False}}, assertion)
    assert_authorized({"logs": {"read": False, "write": True}}, assertion)
    assert_unauthorized({}, assertion)


def test_permissions_and():
    assertion = permissions_and(
        can_read_logs_from_repo(REPO_1), can_write_logs_to_repo(REPO_1)
    )
    assert_unauthorized({"logs": {"read": True, "write": False}}, assertion)
    assert_unauthorized({"logs": {"read": False, "write": True}}, assertion)
    assert_authorized({"logs": {"read": True, "write": True}}, assertion)
