from auditize.accesscontrol.models import AccessRights, LogsRights, EntitiesRights, ReadWritePermissions


def _normalize_repo_permissions(
    repo_perms: dict[str, ReadWritePermissions],
    global_read: bool = False,
    global_write: bool = False,
) -> dict[str, ReadWritePermissions]:
    if global_read and global_write:  # shortcut / optimization
        return {}

    normalized: dict[str, ReadWritePermissions] = {}

    for repo_id, repo_perms in repo_perms.items():
        normalized_repo_perms = ReadWritePermissions(
            read=False if global_read else (repo_perms.read or False),
            write=False if global_write else (repo_perms.write or False),
        )
        if normalized_repo_perms.read or normalized_repo_perms.write:
            normalized[repo_id] = normalized_repo_perms

    return normalized


def _normalize_read_write_permissions(permissions: ReadWritePermissions) -> ReadWritePermissions:
    return ReadWritePermissions(
        read=permissions.read or False,
        write=permissions.write or False,
    )


def normalize_access_rights(rights: AccessRights) -> AccessRights:
    # What kind of normalization do we do:
    # - if superadmin, set all other permissions to False
    # - if logs.read is True, set all logs.repos[repo_id].read permissions to False
    # - if logs.write is True, set all logs.repos[repo_id].write permissions to False
    # - if logs.repos[repo_id] has both read and write permissions set to False, remove it from logs.repos
    # - convert all permissions to False if they are None

    if rights.is_superadmin:
        return AccessRights(
            is_superadmin=True,
            logs=LogsRights(read=False, write=False, repos={}),
            entities=EntitiesRights(
                repos=ReadWritePermissions(read=False, write=False),
                users=ReadWritePermissions(read=False, write=False),
                integrations=ReadWritePermissions(read=False, write=False),
            ),
        )

    return AccessRights(
        is_superadmin=False,
        logs=LogsRights(
            read=rights.logs.read or False,
            write=rights.logs.write or False,
            repos=_normalize_repo_permissions(rights.logs.repos, rights.logs.read, rights.logs.write),
        ),
        entities=EntitiesRights(
            repos=_normalize_read_write_permissions(rights.entities.repos),
            users=_normalize_read_write_permissions(rights.entities.users),
            integrations=_normalize_read_write_permissions(rights.entities.integrations),
        ),
    )
