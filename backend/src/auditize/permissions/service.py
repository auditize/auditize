from uuid import UUID

from auditize.exceptions import PermissionDenied
from auditize.permissions.assertions import PermissionAssertion
from auditize.permissions.models import (
    ApplicableLogPermissions,
    ApplicableLogPermissionScope,
    ApplicablePermissions,
    LogPermissionsInput,
    LogPermissionsOutput,
    ManagementPermissionsOutput,
    Permissions,
    PermissionsInput,
    PermissionsOutput,
    ReadWritePermissionsInput,
    ReadWritePermissionsOutput,
    RepoLogPermissions,
    RepoLogPermissionsInput,
    RepoLogPermissionsOutput,
)
from auditize.permissions.sql_models import ReadableLogEntityPermission


def _normalize_repo_log_permissions(
    repo_log_permissions: list[RepoLogPermissions],
    global_read: bool,
    global_write: bool,
):
    if global_read and global_write:
        repo_log_permissions.clear()
        return

    already_seen_repos: dict[UUID, RepoLogPermissions] = {}

    for perms in list(repo_log_permissions):
        # Handle possible duplicates for a same repo_id, in this case we keep the last one
        already_seen_repo = already_seen_repos.pop(perms.repo_id, None)
        if already_seen_repo:
            repo_log_permissions.remove(already_seen_repo)

        if global_read:
            perms.read = False
        if global_read or perms.read:
            perms.readable_entities.clear()
        if global_write:
            perms.write = False

        if not any((perms.read, perms.readable_entities, perms.write)):
            repo_log_permissions.remove(perms)
        else:
            already_seen_repos[perms.repo_id] = perms


def normalize_permissions(perms: Permissions) -> Permissions:
    # What kind of normalization do we do:
    # - if superadmin, set all other permissions to False
    # - if logs_read is True, set all logs.repos[repo_id].read permissions to False
    # - if logs.write is True, set all logs.repos[repo_id].write permissions to False
    # - if logs.repos[repo_id] has neither read, write nor readable_entities, remove it from logs.repos
    # - if there are duplicates for a same repo_id in logs.repos, keep the last one

    if perms.is_superadmin:
        perms.repos_read = False
        perms.repos_write = False
        perms.users_read = False
        perms.users_write = False
        perms.apikeys_read = False
        perms.apikeys_write = False
        perms.logs_read = False
        perms.logs_write = False
        perms.repo_log_permissions = []
    else:
        _normalize_repo_log_permissions(
            perms.repo_log_permissions, perms.logs_read, perms.logs_write
        )

    return perms


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
            management=ManagementPermissionsOutput(
                repos=ReadWritePermissionsOutput.yes(),
                users=ReadWritePermissionsOutput.yes(),
                apikeys=ReadWritePermissionsOutput.yes(),
            ),
        )
    else:
        return ApplicablePermissions(
            is_superadmin=False,
            logs=ApplicableLogPermissions(
                read=_get_applicable_log_permission_scope(
                    perms.logs_read,
                    any(
                        repo_perms.read or repo_perms.readable_entities
                        for repo_perms in perms.repo_log_permissions
                    ),
                ),
                write=_get_applicable_log_permission_scope(
                    perms.logs_write,
                    any(repo_perms.write for repo_perms in perms.repo_log_permissions),
                ),
            ),
            management=_build_management_permissions_output(perms),
        )


def _update_repo_log_permissions(
    current: RepoLogPermissions,
    update: RepoLogPermissionsInput,
):
    if update.read is not None:
        current.read = update.read
    if update.write is not None:
        current.write = update.write

    if update.readable_entities is not None:
        for updated_readable_entity_ref in update.readable_entities:
            # Add new log entity if not already present
            if updated_readable_entity_ref not in (
                entity.ref for entity in current.readable_entities
            ):
                current.readable_entities.append(
                    ReadableLogEntityPermission(ref=updated_readable_entity_ref)
                )
        # Remove log entities that are not present in the update
        for current_readable_entity in list(current.readable_entities):
            if current_readable_entity.ref not in update.readable_entities:
                current.readable_entities.remove(current_readable_entity)


def _update_log_permissions(
    current: Permissions,
    update: LogPermissionsInput,
):
    if update.read is not None:
        current.logs_read = update.read
    if update.write is not None:
        current.logs_write = update.write

    if update.repos is not None:
        for updated_repo_perms in update.repos:
            current_repo_perms = next(
                (
                    perms
                    for perms in current.repo_log_permissions
                    if perms.repo_id == updated_repo_perms.repo_id
                ),
                None,
            )
            if current_repo_perms:
                if not any(
                    (
                        updated_repo_perms.read,
                        updated_repo_perms.write,
                        updated_repo_perms.readable_entities,
                    )
                ):
                    # Remove repo log permissions that are said to be removed
                    current.repo_log_permissions.remove(current_repo_perms)
                else:
                    # Update existing repo log permissions
                    _update_repo_log_permissions(current_repo_perms, updated_repo_perms)
            else:
                # Add new repo log permissions
                new_repo_perms = RepoLogPermissions(repo_id=updated_repo_perms.repo_id)
                _update_repo_log_permissions(new_repo_perms, updated_repo_perms)
                current.repo_log_permissions.append(new_repo_perms)


def update_permissions(
    current: Permissions,
    update: PermissionsInput,
):
    # Superadmin
    if update.is_superadmin is not None:
        current.is_superadmin = update.is_superadmin

    # Repos management
    if update.management.repos.read is not None:
        current.repos_read = update.management.repos.read
    if update.management.repos.write is not None:
        current.repos_write = update.management.repos.write

    # Users management
    if update.management.users.read is not None:
        current.users_read = update.management.users.read
    if update.management.users.write is not None:
        current.users_write = update.management.users.write

    # API keys management
    if update.management.apikeys.read is not None:
        current.apikeys_read = update.management.apikeys.read
    if update.management.apikeys.write is not None:
        current.apikeys_write = update.management.apikeys.write

    # Logs
    _update_log_permissions(current, update.logs)

    # Normalize permissions
    normalize_permissions(current)


def build_permissions(input: PermissionsInput) -> Permissions:
    perms = Permissions()
    update_permissions(perms, input)
    return perms


def _build_management_permissions_output(
    perms: Permissions,
) -> ManagementPermissionsOutput:
    return ManagementPermissionsOutput(
        repos=ReadWritePermissionsOutput(
            read=perms.repos_read,
            write=perms.repos_write,
        ),
        users=ReadWritePermissionsOutput(
            read=perms.users_read,
            write=perms.users_write,
        ),
        apikeys=ReadWritePermissionsOutput(
            read=perms.apikeys_read,
            write=perms.apikeys_write,
        ),
    )


def build_permissions_output(perms: Permissions) -> PermissionsOutput:
    return PermissionsOutput(
        is_superadmin=perms.is_superadmin,
        management=_build_management_permissions_output(perms),
        logs=LogPermissionsOutput(
            read=perms.logs_read,
            write=perms.logs_write,
            repos=[
                RepoLogPermissionsOutput(
                    repo_id=repo_log_perms.repo_id,
                    read=repo_log_perms.read,
                    write=repo_log_perms.write,
                    readable_entities=[
                        readable_entity.ref
                        for readable_entity in repo_log_perms.readable_entities
                    ],
                )
                for repo_log_perms in perms.repo_log_permissions
            ],
        ),
    )


def _authorize_grant(assignee_perm: bool | None, grantor_perm: bool, name: str):
    if assignee_perm in (True, False) and not grantor_perm:
        raise PermissionDenied(
            f"Insufficient grantor permissions to grant {name!r} permission"
        )


def _authorize_rw_perms_grant(
    assignee_perms: ReadWritePermissionsInput,
    grantor_perms_read: bool,
    grantor_perms_write: bool,
    name: str,
):
    _authorize_grant(assignee_perms.read, grantor_perms_read, f"{name} read")
    _authorize_grant(assignee_perms.write, grantor_perms_write, f"{name} write")


def authorize_grant(grantor_perms: Permissions, assignee_perms: PermissionsInput):
    # if superadmin, can grant anything
    if grantor_perms.is_superadmin:
        return

    if assignee_perms.is_superadmin is not None:
        raise PermissionDenied("Cannot alter superadmin role")

    # Check logs.{read,write} grants
    _authorize_rw_perms_grant(
        assignee_perms.logs,
        grantor_perms.logs_read,
        grantor_perms.logs_write,
        "logs",
    )

    # Check logs.repos.{read,write} grants
    # if grantor has logs.read and logs.write, he can grant anything:
    if not (grantor_perms.logs_read and grantor_perms.logs_write):
        for assignee_repo_perms in assignee_perms.logs.repos:
            grantor_repo_perms = grantor_perms.get_repo_log_permissions_by_id(
                assignee_repo_perms.repo_id
            )
            _authorize_grant(
                assignee_repo_perms.read,
                bool(
                    (grantor_repo_perms and grantor_repo_perms.read)
                    or grantor_perms.logs_read
                ),
                f"logs read on repo {assignee_repo_perms.repo_id}",
            )
            _authorize_grant(
                bool(assignee_repo_perms.readable_entities)
                if assignee_repo_perms.readable_entities is not None
                else None,
                bool(
                    (grantor_repo_perms and grantor_repo_perms.read)
                    or grantor_perms.logs_read
                ),
                f"logs read on repo {assignee_repo_perms.repo_id}",
            )
            _authorize_grant(
                assignee_repo_perms.write,
                bool(
                    (grantor_repo_perms and grantor_repo_perms.write)
                    or grantor_perms.logs_write
                ),
                f"logs write on repo {assignee_repo_perms.repo_id}",
            )

    # Check management.{repos,users,apikeys} grants
    _authorize_rw_perms_grant(
        assignee_perms.management.repos,
        grantor_perms.repos_read,
        grantor_perms.repos_write,
        "repos",
    )
    _authorize_rw_perms_grant(
        assignee_perms.management.users,
        grantor_perms.users_read,
        grantor_perms.users_write,
        "users",
    )
    _authorize_rw_perms_grant(
        assignee_perms.management.apikeys,
        grantor_perms.apikeys_read,
        grantor_perms.apikeys_write,
        "apikeys",
    )


def is_authorized(perms: Permissions, assertion: PermissionAssertion) -> bool:
    return assertion(perms)


def authorize_access(perms: Permissions, assertion: PermissionAssertion) -> None:
    if not is_authorized(perms, assertion):
        raise PermissionDenied()
