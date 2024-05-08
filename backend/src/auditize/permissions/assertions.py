from dataclasses import dataclass
from functools import partial
from typing import Callable

from auditize.permissions.models import Permissions

__all__ = (
    "PermissionAssertion",
    "can_read_logs",
    "can_write_logs",
    "can_read_repos",
    "can_write_repos",
    "can_read_users",
    "can_write_users",
    "can_read_apikeys",
    "can_write_apikeys",
    "permissions_and",
    "permissions_or",
)

PermissionAssertion = Callable[[Permissions], bool]


@dataclass
class LogPermissionAssertion:
    permission_type: str  # "read" or "write"
    repo_id: str = None

    def __call__(self, perms: Permissions) -> bool:
        if perms.is_superadmin:
            return True

        if self.permission_type == "read":
            if perms.logs.read:
                return True
            if self.repo_id is None:
                return False
            repo_perms = perms.logs.repos.get(self.repo_id)
            return bool(repo_perms and repo_perms.read)

        if self.permission_type == "write":
            if perms.logs.write:
                return True
            if self.repo_id is None:
                return False
            repo_perms = perms.logs.repos.get(self.repo_id)
            return bool(repo_perms and repo_perms.write)

        raise Exception(
            f"Invalid log permission type: {self.permission_type}"
        )  # pragma: no cover, cannot happen


def can_read_logs(repo_id: str = None) -> PermissionAssertion:
    return LogPermissionAssertion(permission_type="read", repo_id=repo_id)


def can_write_logs(repo_id: str = None) -> PermissionAssertion:
    return LogPermissionAssertion(permission_type="write", repo_id=repo_id)


@dataclass
class EntityPermissionAssertion:
    permission_type: str  # "read" or "write"
    entity_type: str  # "repos", "users" or "apikeys"

    def __call__(self, perms: Permissions) -> bool:
        if perms.is_superadmin:
            return True

        if self.entity_type == "repos":
            entity_perms = perms.management.repos
        elif self.entity_type == "users":
            entity_perms = perms.management.users
        elif self.entity_type == "apikeys":
            entity_perms = perms.management.apikeys
        else:
            raise Exception(
                f"Invalid entity type: {self.entity_type}"
            )  # pragma: no cover, cannot happen

        if self.permission_type == "read":
            return bool(entity_perms.read)
        if self.permission_type == "write":
            return bool(entity_perms.write)

        raise Exception(
            f"Invalid entity permission type: {self.permission_type}"
        )  # pragma: no cover, cannot happen


can_read_repos = partial(
    EntityPermissionAssertion, permission_type="read", entity_type="repos"
)
can_write_repos = partial(
    EntityPermissionAssertion, permission_type="write", entity_type="repos"
)
can_read_users = partial(
    EntityPermissionAssertion, permission_type="read", entity_type="users"
)
can_write_users = partial(
    EntityPermissionAssertion, permission_type="write", entity_type="users"
)
can_read_apikeys = partial(
    EntityPermissionAssertion, permission_type="read", entity_type="apikeys"
)
can_write_apikeys = partial(
    EntityPermissionAssertion, permission_type="write", entity_type="apikeys"
)


def permissions_and(*assertions: PermissionAssertion) -> PermissionAssertion:
    def func(perms: Permissions) -> bool:
        return all(assertion(perms) for assertion in assertions)

    return func


def permissions_or(*assertions: PermissionAssertion) -> PermissionAssertion:
    def func(perms: Permissions) -> bool:
        return any(assertion(perms) for assertion in assertions)

    return func
