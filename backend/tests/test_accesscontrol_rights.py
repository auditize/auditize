from auditize.accesscontrol.models import AccessRights
from auditize.accesscontrol.rights import normalize_access_rights


def _test_access_rights_normalization(input: dict, expected: dict):
    input = AccessRights.model_validate(input)

    assert normalize_access_rights(input).model_dump() == expected


def test_normalization_superadmin_only():
    _test_access_rights_normalization(
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
    _test_access_rights_normalization(
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
    _test_access_rights_normalization(
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
    _test_access_rights_normalization(
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
    _test_access_rights_normalization(
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
    _test_access_rights_normalization(
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
