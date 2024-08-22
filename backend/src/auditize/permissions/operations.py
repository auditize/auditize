from uuid import UUID

from auditize.exceptions import PermissionDenied
from auditize.permissions.assertions import PermissionAssertion
from auditize.permissions.models import (
    ApplicableLogPermissions,
    ApplicableLogPermissionScope,
    ApplicablePermissions,
    LogPermissions,
    ManagementPermissions,
    Permissions,
    ReadWritePermissions,
    RepoLogPermissions,
)

__all__ = (
    "normalize_permissions",
    "authorize_grant",
    "update_permissions",
    "authorize_access",
    "compute_applicable_permissions",
    "is_authorized",
)


def _normalize_repo_permissions(
    repo_perms: list[RepoLogPermissions],
    global_read: bool = False,
    global_write: bool = False,
) -> list[RepoLogPermissions]:
    if global_read and global_write:  # shortcut / optimization
        return []

    # the function uses internally a dict to normalize the permissions to handle possible duplicates
    # between repo_id (the last permission line wins)
    normalized: dict[UUID, RepoLogPermissions] = {}

    for single_repo_perms in repo_perms:
        read = False if global_read else (single_repo_perms.read or False)
        write = False if global_write else (single_repo_perms.write or False)
        normalized[single_repo_perms.repo_id] = RepoLogPermissions(
            repo_id=single_repo_perms.repo_id,
            read=read,
            write=write,
            readable_entities=(single_repo_perms.readable_entities or [])
            if read
            else [],
        )

    return [perms for perms in normalized.values() if perms.read or perms.write]


def _normalize_read_write_permissions(
    permissions: ReadWritePermissions,
) -> ReadWritePermissions:
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
            logs=LogPermissions(read=False, write=False, repos=[]),
            management=ManagementPermissions(
                repos=ReadWritePermissions.no(),
                users=ReadWritePermissions.no(),
                apikeys=ReadWritePermissions.no(),
            ),
        )

    return Permissions(
        is_superadmin=False,
        logs=LogPermissions(
            read=perms.logs.read or False,
            write=perms.logs.write or False,
            repos=_normalize_repo_permissions(
                perms.logs.repos, perms.logs.read, perms.logs.write
            ),
        ),
        management=ManagementPermissions(
            repos=_normalize_read_write_permissions(perms.management.repos),
            users=_normalize_read_write_permissions(perms.management.users),
            apikeys=_normalize_read_write_permissions(perms.management.apikeys),
        ),
    )


def _get_applicable_log_permission_scope(
    on_all: bool, on_repos: bool
) -> ApplicableLogPermissionScope:
    if on_all:
        return "all"
    if on_repos:
        return "partial"
    return "none"


def compute_applicable_permissions(perms: Permissions) -> ApplicablePermissions:
    if perms.is_superadmin:
        return ApplicablePermissions(
            is_superadmin=True,
            logs=ApplicableLogPermissions(read="all", write="all"),
            management=ManagementPermissions(
                repos=ReadWritePermissions.yes(),
                users=ReadWritePermissions.yes(),
                apikeys=ReadWritePermissions.yes(),
            ),
        )
    else:
        return ApplicablePermissions(
            is_superadmin=False,
            logs=ApplicableLogPermissions(
                read=_get_applicable_log_permission_scope(
                    perms.logs.read,
                    any(repo_perms.read for repo_perms in perms.logs.repos),
                ),
                write=_get_applicable_log_permission_scope(
                    perms.logs.write,
                    any(repo_perms.write for repo_perms in perms.logs.repos),
                ),
            ),
            management=perms.management.model_copy(deep=True),
        )


def _authorize_grant(assignee_perm: bool | None, grantor_perm: bool, name: str):
    if assignee_perm in (True, False) and not grantor_perm:
        raise PermissionDenied(
            f"Insufficient grantor permissions to grant {name!r} permission"
        )


def _authorize_rw_perms_grant(
    assignee_perms: ReadWritePermissions, grantor_perms: ReadWritePermissions, name: str
):
    _authorize_grant(assignee_perms.read, grantor_perms.read, f"{name} read")
    _authorize_grant(assignee_perms.write, grantor_perms.write, f"{name} write")


def authorize_grant(grantor_perms: Permissions, assignee_perms: Permissions):
    # if superadmin, can grant anything
    if grantor_perms.is_superadmin:
        return

    if assignee_perms.is_superadmin is not None:
        raise PermissionDenied("Cannot alter superadmin role")

    # Check logs.{read,write} grants
    _authorize_rw_perms_grant(assignee_perms.logs, grantor_perms.logs, "logs")

    # Check logs.repos.{read,write} grants
    # if grantor has logs.read and logs.write, he can grant anything:
    if not (grantor_perms.logs.read and grantor_perms.logs.write):
        for assignee_repo_perms in assignee_perms.logs.repos:
            grantor_repo_perms = grantor_perms.logs.get_repo_permissions(
                assignee_repo_perms.repo_id
            )
            _authorize_grant(
                assignee_repo_perms.read,
                (
                    grantor_repo_perms
                    and grantor_repo_perms.read
                    # grantor must have global access to the repo, not a entity subset, to grant read access:
                    and not grantor_repo_perms.readable_entities
                )
                or grantor_perms.logs.read,
                f"logs read on repo {assignee_repo_perms.repo_id}",
            )
            _authorize_grant(
                assignee_repo_perms.write,
                (grantor_repo_perms and grantor_repo_perms.write)
                or grantor_perms.logs.write,
                f"logs write on repo {assignee_repo_perms.repo_id}",
            )

    # Check management.{repos,users,apikeys} grants
    _authorize_rw_perms_grant(
        assignee_perms.management.repos, grantor_perms.management.repos, "repos"
    )
    _authorize_rw_perms_grant(
        assignee_perms.management.users, grantor_perms.management.users, "users"
    )
    _authorize_rw_perms_grant(
        assignee_perms.management.apikeys,
        grantor_perms.management.apikeys,
        "apikeys",
    )


def _update_permission(orig: bool, update: bool | None) -> bool:
    return update if update is not None else orig


def _update_rw_permissions(
    orig_perms: ReadWritePermissions, update_perms: ReadWritePermissions
) -> ReadWritePermissions:
    return ReadWritePermissions(
        read=_update_permission(orig_perms.read, update_perms.read),
        write=_update_permission(orig_perms.write, update_perms.write),
    )


def update_permissions(
    orig_perms: Permissions, update_perms: Permissions
) -> Permissions:
    new = Permissions()

    # Update superadmin role
    new.is_superadmin = _update_permission(
        orig_perms.is_superadmin, update_perms.is_superadmin
    )

    # Update logs permissions
    new.logs.read = _update_permission(orig_perms.logs.read, update_perms.logs.read)
    new.logs.write = _update_permission(orig_perms.logs.write, update_perms.logs.write)
    all_repo_perms = {perms.repo_id: perms for perms in orig_perms.logs.repos}
    for update_repo_perms in update_perms.logs.repos:
        if update_repo_perms.read is False and update_repo_perms.write is False:
            all_repo_perms.pop(update_repo_perms.repo_id, None)
        else:
            orig_repo_perms = all_repo_perms.get(update_repo_perms.repo_id)
            all_repo_perms[update_repo_perms.repo_id] = RepoLogPermissions(
                repo_id=update_repo_perms.repo_id,
                read=_update_permission(
                    orig_repo_perms and orig_repo_perms.read, update_repo_perms.read
                ),
                write=_update_permission(
                    orig_repo_perms and orig_repo_perms.write, update_repo_perms.write
                ),
                readable_entities=(
                    update_repo_perms.readable_entities
                    if update_repo_perms.readable_entities is not None
                    else (orig_repo_perms.readable_entities if orig_repo_perms else [])
                ),
            )
    new.logs.repos = list(all_repo_perms.values())

    # Update management permissions
    new.management.repos = _update_rw_permissions(
        orig_perms.management.repos, update_perms.management.repos
    )
    new.management.users = _update_rw_permissions(
        orig_perms.management.users, update_perms.management.users
    )
    new.management.apikeys = _update_rw_permissions(
        orig_perms.management.apikeys, update_perms.management.apikeys
    )

    # Return a normalized result
    return normalize_permissions(new)


def is_authorized(perms: Permissions, assertion: PermissionAssertion) -> bool:
    return assertion(perms)


def authorize_access(perms: Permissions, assertion: PermissionAssertion) -> None:
    if not is_authorized(perms, assertion):
        raise PermissionDenied()
