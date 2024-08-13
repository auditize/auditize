from dataclasses import dataclass
from functools import partial
from typing import Callable
from uuid import UUID

from auditize.permissions.models import Permissions

__all__ = (
    "PermissionAssertion",
    "can_read_logs",
    "can_write_logs",
    "can_read_repo",
    "can_write_repo",
    "can_read_user",
    "can_write_user",
    "can_read_apikey",
    "can_write_apikey",
    "permissions_and",
    "permissions_or",
)

PermissionAssertion = Callable[[Permissions], bool]


@dataclass
class LogPermissionAssertion:
    permission_type: str  # "read" or "write"
    repo_id: UUID = None

    def __call__(self, perms: Permissions) -> bool:
        if perms.is_superadmin:
            return True

        if self.permission_type == "read":
            if perms.logs.read:
                return True
            if self.repo_id is None:
                return False
            return any(
                repo_perms.repo_id == self.repo_id and repo_perms.read
                for repo_perms in perms.logs.repos
            )

        if self.permission_type == "write":
            if perms.logs.write:
                return True
            if self.repo_id is None:
                return False
            return any(
                repo_perms.repo_id == self.repo_id and repo_perms.write
                for repo_perms in perms.logs.repos
            )

        raise Exception(
            f"Invalid log permission type: {self.permission_type}"
        )  # pragma: no cover, cannot happen


def can_read_logs(repo_id: UUID = None) -> PermissionAssertion:
    return LogPermissionAssertion(permission_type="read", repo_id=repo_id)


def can_write_logs(repo_id: UUID = None) -> PermissionAssertion:
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


can_read_repo = partial(
    EntityPermissionAssertion, permission_type="read", entity_type="repos"
)
can_write_repo = partial(
    EntityPermissionAssertion, permission_type="write", entity_type="repos"
)
can_read_user = partial(
    EntityPermissionAssertion, permission_type="read", entity_type="users"
)
can_write_user = partial(
    EntityPermissionAssertion, permission_type="write", entity_type="users"
)
can_read_apikey = partial(
    EntityPermissionAssertion, permission_type="read", entity_type="apikeys"
)
can_write_apikey = partial(
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
