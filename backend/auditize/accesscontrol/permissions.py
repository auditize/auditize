from dataclasses import dataclass
from functools import partial
from typing import Callable

from auditize.accesscontrol.models import AccessRights
from auditize.common.exceptions import PermissionDenied

PermissionAssertion = Callable[[AccessRights], bool]


@dataclass
class LogPermissionAssertion:
    type: str  # "read" or "write"
    repo_id: str

    def __call__(self, rights: AccessRights) -> bool:
        if rights.is_superadmin:
            return True

        if self.type == "read":
            if rights.logs.read:
                return True
            repo_perms = rights.logs.repos.get(self.repo_id)
            return bool(repo_perms and repo_perms.read)

        if self.type == "write":
            if rights.logs.write:
                return True
            repo_perms = rights.logs.repos.get(self.repo_id)
            return bool(repo_perms and repo_perms.write)

        raise Exception(f"Invalid log permission type: {self.type}")  # pragma: no cover, cannot happen


def can_read_logs(repo_id: str) -> PermissionAssertion:
    return LogPermissionAssertion(type="read", repo_id=repo_id)


def can_write_logs(repo_id: str) -> PermissionAssertion:
    return LogPermissionAssertion(type="write", repo_id=repo_id)


@dataclass
class EntityPermissionAssertion:
    permission_type: str  # "read" or "write"
    entity_type: str  # "repos", "users" or "integrations"

    def __call__(self, rights: AccessRights) -> bool:
        if rights.is_superadmin:
            return True

        if self.entity_type == "repos":
            entity_perms = rights.entities.repos
        elif self.entity_type == "users":
            entity_perms = rights.entities.users
        elif self.entity_type == "integrations":
            entity_perms = rights.entities.integrations
        else:
            raise Exception(f"Invalid entity type: {self.entity_type}")  # pragma: no cover, cannot happen

        if self.permission_type == "read":
            return entity_perms.read
        if self.permission_type == "write":
            return entity_perms.write

        raise Exception(f"Invalid entity permission type: {self.permission_type}")  # pragma: no cover, cannot happen


can_read_repos = partial(EntityPermissionAssertion, permission_type="read", entity_type="repos")
can_write_repos = partial(EntityPermissionAssertion, permission_type="write", entity_type="repos")
can_read_users = partial(EntityPermissionAssertion, permission_type="read", entity_type="users")
can_write_users = partial(EntityPermissionAssertion, permission_type="write", entity_type="users")
can_read_integrations = partial(EntityPermissionAssertion, permission_type="read", entity_type="integrations")
can_write_integrations = partial(EntityPermissionAssertion, permission_type="write", entity_type="integrations")


def permissions_and(*assertions: PermissionAssertion) -> PermissionAssertion:
    def func(rights: AccessRights) -> bool:
        return all(assertion(rights) for assertion in assertions)

    return func


def permissions_or(*assertions: PermissionAssertion) -> PermissionAssertion:
    def func(rights: AccessRights) -> bool:
        return any(assertion(rights) for assertion in assertions)

    return func


def authorize_access(rights: AccessRights, assertion: PermissionAssertion) -> None:
    if not assertion(rights):
        raise PermissionDenied("Access denied")
