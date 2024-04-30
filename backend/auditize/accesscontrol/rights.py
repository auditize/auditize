from auditize.accesscontrol.models import AccessRights, LogsRights, EntitiesRights, ReadWritePermissions
from auditize.common.exceptions import PermissionDenied


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


def _authorize_grant(target_right: bool | None, base_right: bool, name: str):
    if target_right in (True, False) and not base_right:
        raise PermissionDenied(f"Insufficient rights to grant {name!r} rights")


def _authorize_rw_perm_grant(target_right: ReadWritePermissions, base_right: ReadWritePermissions, name: str):
    _authorize_grant(target_right.read, base_right.read, f"{name} read")
    _authorize_grant(target_right.write, base_right.write, f"{name} write")


def authorize_grant(rights: AccessRights, target_rights: AccessRights):
    # optimization: if superadmin, can grant anything
    if rights.is_superadmin:
        return

    if target_rights.is_superadmin is not None:
        raise PermissionDenied("Cannot grant superadmin rights")

    # Check logs.{read,write} grants
    _authorize_rw_perm_grant(target_rights.logs, rights.logs, "logs")

    # Check logs.repos.{read,write} grants
    # optimization: if logs.read and logs.write, can grant anything:
    if not (target_rights.logs.read and target_rights.logs.write):
        for target_repo_id, target_repo_perms in target_rights.logs.repos.items():
            repo_rights = rights.logs.repos.get(target_repo_id, ReadWritePermissions(read=False, write=False))
            _authorize_grant(
                target_repo_perms.read, repo_rights.read or rights.logs.read, f"logs read on repo {target_repo_id}"
            )
            _authorize_grant(
                target_repo_perms.write, repo_rights.write or rights.logs.write, f"logs write on repo {target_repo_id}"
            )

    # Check entities.{repos,users,integrations} grants
    _authorize_rw_perm_grant(target_rights.entities.repos, rights.entities.repos, "repos")
    _authorize_rw_perm_grant(target_rights.entities.users, rights.entities.users, "users")
    _authorize_rw_perm_grant(target_rights.entities.integrations, rights.entities.integrations, "integrations")


def _update_permission(orig: bool, update: bool | None) -> bool:
    return update if update is not None else orig


def _update_rw_permissions(orig: ReadWritePermissions, update: ReadWritePermissions) -> ReadWritePermissions:
    return ReadWritePermissions(
        read=_update_permission(orig.read, update.read),
        write=_update_permission(orig.write, update.write),
    )


def update_permissions(orig: AccessRights, update: AccessRights) -> AccessRights:
    new = AccessRights()

    # Update superadmin role
    new.is_superadmin = _update_permission(orig.is_superadmin, update.is_superadmin)

    # Update logs permissions
    new.logs.read = _update_permission(orig.logs.read, update.logs.read)
    new.logs.write = _update_permission(orig.logs.write, update.logs.write)
    for update_repo_id, update_repo_perms in update.logs.repos.items():
        orig_repo_perms = orig.logs.repos.get(update_repo_id, ReadWritePermissions(read=False, write=False))
        new.logs.repos[update_repo_id] = _update_rw_permissions(orig_repo_perms, update_repo_perms)

    # Update entities permissions
    new.entities.repos = _update_rw_permissions(orig.entities.repos, update.entities.repos)
    new.entities.users = _update_rw_permissions(orig.entities.users, update.entities.users)
    new.entities.integrations = _update_rw_permissions(orig.entities.integrations, update.entities.integrations)

    # Return a normalized result
    return normalize_access_rights(new)
