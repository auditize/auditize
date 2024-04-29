from auditize.accesscontrol.models import AccessRights, ReadWritePermissions


def _normalize_repo_permissions(
    repo_perms: dict[str, ReadWritePermissions],
    global_read: bool = False,
    global_write: bool = False,
) -> dict[str, ReadWritePermissions]:
    if global_read and global_write:  # shortcut / optimization
        return {}

    normalized: dict[str, ReadWritePermissions] = {}

    for repo_id, repo_perms in repo_perms.items():
        normalized_repo_perms = repo_perms.model_copy(
            update={
                "read": False if global_read else repo_perms.read,
                "write": False if global_write else repo_perms.write,
            }
        )
        if normalized_repo_perms.read or normalized_repo_perms.write:
            normalized[repo_id] = normalized_repo_perms

    return normalized


def normalize_access_rights(rights: AccessRights) -> AccessRights:
    if rights.is_superadmin:
        # cleanup all specific permissions
        return AccessRights(is_superadmin=True)

    if rights.logs.read or rights.logs.write:
        # cleanup specific permissions on specific repositories
        return rights.model_copy(
            update={"logs": rights.logs.model_copy(
                update={"repos": _normalize_repo_permissions(rights.logs.repos, rights.logs.read, rights.logs.write)}
            )}
        )

    return rights
