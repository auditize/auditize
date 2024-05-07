DEFAULT_PERMISSIONS = {
    "is_superadmin": False,
    "logs": {"read": False, "write": False, "repos": {}},
    "entities": {
        "repos": {"read": False, "write": False},
        "users": {"read": False, "write": False},
        "integrations": {"read": False, "write": False},
    },
}

DEFAULT_APPLICABLE_PERMISSIONS = {
    "is_superadmin": False,
    "logs": {
        "read": "none",
        "write": "none",
    },
    "entities": {
        "repos": {"read": False, "write": False},
        "users": {"read": False, "write": False},
        "integrations": {"read": False, "write": False},
    },
}


SUPERADMIN_APPLICABLE_PERMISSIONS = {
    "is_superadmin": True,
    "logs": {
        "read": "all",
        "write": "all",
    },
    "entities": {
        "repos": {"read": True, "write": True},
        "users": {"read": True, "write": True},
        "integrations": {"read": True, "write": True},
    },
}
