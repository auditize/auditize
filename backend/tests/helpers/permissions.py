DEFAULT_PERMISSIONS = {
    "is_superadmin": False,
    "logs": {
        "read": False,
        "write": False,
        "repos": {}
    },
    "entities": {
        "repos": {"read": False, "write": False},
        "users": {"read": False, "write": False},
        "integrations": {"read": False, "write": False},
    },
}
