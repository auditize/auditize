from auditize.accesscontrol.models import AccessRights
from auditize.accesscontrol.rights import normalize_access_rights


def _test_access_rights_normalization(actual: dict, expected: dict):
    actual = AccessRights.model_validate(actual)
    expected = AccessRights.model_validate(expected)

    assert normalize_access_rights(actual).model_dump() == expected.model_dump()


def test_normalization_superadmin_only():
    _test_access_rights_normalization(
        {"is_superadmin": True},
        {"is_superadmin": True},
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
        {"is_superadmin": True},
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
        {"is_superadmin": True},
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
            "logs": {
                "read": True,
                "write": False,
                "repos": {
                    "repo1": {"read": False, "write": True},
                    "repo2": {"read": False, "write": True}
                },
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
            "logs": {
                "read": False,
                "write": True,
                "repos": {
                    "repo1": {"read": True, "write": False},
                    "repo3": {"read": True, "write": False},
                },
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
            "logs": {
                "read": True,
                "write": True,
                "repos": {},
            },
        },
    )
