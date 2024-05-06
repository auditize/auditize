from auditize.permissions.assertions import PermissionAssertion
from auditize.permissions.models import Permissions, LogsPermissions, EntitiesPermissions, ReadWritePermissions, ApplicablePermissions
from auditize.common.exceptions import PermissionDenied


__all__ = ("normalize_permissions", "authorize_grant", "update_permissions", "authorize_access", "get_applicable_permissions", "is_authorized")


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


def normalize_permissions(perms: Permissions) -> Permissions:
    # What kind of normalization do we do:
    # - if superadmin, set all other permissions to False
    # - if logs.read is True, set all logs.repos[repo_id].read permissions to False
    # - if logs.write is True, set all logs.repos[repo_id].write permissions to False
    # - if logs.repos[repo_id] has both read and write permissions set to False, remove it from logs.repos
    # - convert all permissions to False if they are None

    if perms.is_superadmin:
        return Permissions(
            is_superadmin=True,
            logs=LogsPermissions(read=False, write=False, repos={}),
            entities=EntitiesPermissions(
                repos=ReadWritePermissions.no(),
                users=ReadWritePermissions.no(),
                integrations=ReadWritePermissions.no(),
            ),
        )

    return Permissions(
        is_superadmin=False,
        logs=LogsPermissions(
            read=perms.logs.read or False,
            write=perms.logs.write or False,
            repos=_normalize_repo_permissions(perms.logs.repos, perms.logs.read, perms.logs.write),
        ),
        entities=EntitiesPermissions(
            repos=_normalize_read_write_permissions(perms.entities.repos),
            users=_normalize_read_write_permissions(perms.entities.users),
            integrations=_normalize_read_write_permissions(perms.entities.integrations),
        ),
    )


def get_applicable_permissions(perms: Permissions) -> ApplicablePermissions:
    if perms.is_superadmin:
        return ApplicablePermissions(
            is_superadmin=True,
            logs=LogsPermissions.yes(),
            entities=EntitiesPermissions(
                repos=ReadWritePermissions.yes(),
                users=ReadWritePermissions.yes(),
                integrations=ReadWritePermissions.yes(),
            ),
        )
    else:
        return ApplicablePermissions(
            is_superadmin=False,
            logs=ReadWritePermissions(read=perms.logs.read, write=perms.logs.write),
            entities=perms.entities.model_copy(deep=True),
        )


def _authorize_grant(assignee_perm: bool | None, grantor_perm: bool, name: str):
    if assignee_perm in (True, False) and not grantor_perm:
        raise PermissionDenied(f"Insufficient grantor permissions to grant {name!r} permission")


def _authorize_rw_perms_grant(assignee_perms: ReadWritePermissions, grantor_perms: ReadWritePermissions, name: str):
    _authorize_grant(assignee_perms.read, grantor_perms.read, f"{name} read")
    _authorize_grant(assignee_perms.write, grantor_perms.write, f"{name} write")


def authorize_grant(grantor_perms: Permissions, assignee_perms: Permissions):
    # optimization: if superadmin, can grant anything
    if grantor_perms.is_superadmin:
        return

    if assignee_perms.is_superadmin is not None:
        raise PermissionDenied("Cannot alter superadmin role")

    # Check logs.{read,write} grants
    _authorize_rw_perms_grant(assignee_perms.logs, grantor_perms.logs, "logs")

    # Check logs.repos.{read,write} grants
    # optimization: if grantor has logs.read and logs.write, he can grant anything:
    if not (grantor_perms.logs.read and grantor_perms.logs.write):
        for assignee_repo_id, assignee_repo_perms in assignee_perms.logs.repos.items():
            grantor_repo_perms = grantor_perms.logs.repos.get(assignee_repo_id, ReadWritePermissions.no())
            _authorize_grant(
                assignee_repo_perms.read, grantor_repo_perms.read or grantor_perms.logs.read, f"logs read on repo {assignee_repo_id!r}"
            )
            _authorize_grant(
                assignee_repo_perms.write, grantor_repo_perms.write or grantor_perms.logs.write, f"logs write on repo {assignee_repo_id!r}"
            )

    # Check entities.{repos,users,integrations} grants
    _authorize_rw_perms_grant(assignee_perms.entities.repos, grantor_perms.entities.repos, "repos")
    _authorize_rw_perms_grant(assignee_perms.entities.users, grantor_perms.entities.users, "users")
    _authorize_rw_perms_grant(assignee_perms.entities.integrations, grantor_perms.entities.integrations, "integrations")


def _update_permission(orig: bool, update: bool | None) -> bool:
    return update if update is not None else orig


def _update_rw_permissions(orig_perms: ReadWritePermissions, update_perms: ReadWritePermissions) -> ReadWritePermissions:
    return ReadWritePermissions(
        read=_update_permission(orig_perms.read, update_perms.read),
        write=_update_permission(orig_perms.write, update_perms.write),
    )


def update_permissions(orig_perms: Permissions, update_perms: Permissions) -> Permissions:
    new = Permissions()

    # Update superadmin role
    new.is_superadmin = _update_permission(orig_perms.is_superadmin, update_perms.is_superadmin)

    # Update logs permissions
    new.logs.read = _update_permission(orig_perms.logs.read, update_perms.logs.read)
    new.logs.write = _update_permission(orig_perms.logs.write, update_perms.logs.write)
    for update_repo_id, update_repo_perms in update_perms.logs.repos.items():
        orig_repo_perms = orig_perms.logs.repos.get(update_repo_id, ReadWritePermissions.no())
        new.logs.repos[update_repo_id] = _update_rw_permissions(orig_repo_perms, update_repo_perms)

    # Update entities permissions
    new.entities.repos = _update_rw_permissions(orig_perms.entities.repos, update_perms.entities.repos)
    new.entities.users = _update_rw_permissions(orig_perms.entities.users, update_perms.entities.users)
    new.entities.integrations = _update_rw_permissions(orig_perms.entities.integrations, update_perms.entities.integrations)

    # Return a normalized result
    return normalize_permissions(new)


def is_authorized(perms: Permissions, assertion: PermissionAssertion) -> bool:
    return assertion(perms)


def authorize_access(perms: Permissions, assertion: PermissionAssertion) -> None:
    if not is_authorized(perms, assertion):
        raise PermissionDenied("Access denied")
