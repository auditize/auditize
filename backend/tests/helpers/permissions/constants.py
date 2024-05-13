DEFAULT_PERMISSIONS = {
    "is_superadmin": False,
    "logs": {"read": False, "write": False, "repos": []},
    "management": {
        "repos": {"read": False, "write": False},
        "users": {"read": False, "write": False},
        "apikeys": {"read": False, "write": False},
    },
}

DEFAULT_APPLICABLE_PERMISSIONS = {
    "is_superadmin": False,
    "logs": {
        "read": "none",
        "write": "none",
    },
    "management": {
        "repos": {"read": False, "write": False},
        "users": {"read": False, "write": False},
        "apikeys": {"read": False, "write": False},
    },
}

SUPERADMIN_APPLICABLE_PERMISSIONS = {
    "is_superadmin": True,
    "logs": {
        "read": "all",
        "write": "all",
    },
    "management": {
        "repos": {"read": True, "write": True},
        "users": {"read": True, "write": True},
        "apikeys": {"read": True, "write": True},
    },
}
