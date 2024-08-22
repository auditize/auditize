from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

__all__ = (
    "ApplicableLogPermissions",
    "ApplicableLogPermissionScope",
    "ApplicablePermissions",
    "ReadWritePermissions",
    "ManagementPermissions",
    "RepoLogPermissions",
    "LogPermissions",
    "Permissions",
)


class ReadWritePermissions(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def no(cls) -> "ReadWritePermissions":
        return cls(read=False, write=False)

    @classmethod
    def yes(cls) -> "ReadWritePermissions":
        return cls(read=True, write=True)


class ManagementPermissions(BaseModel):
    repos: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    users: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    apikeys: ReadWritePermissions = Field(default_factory=ReadWritePermissions)

    model_config = ConfigDict(extra="forbid")


class RepoLogPermissions(ReadWritePermissions):
    repo_id: UUID
    readable_entities: list[str] | None = Field(default=None)

    model_config = ConfigDict(extra="forbid")


class LogPermissions(ReadWritePermissions):
    repos: list[RepoLogPermissions] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    def get_repos(self, *, can_read=False, can_write=False) -> list[UUID]:
        def perms_ok(perms: ReadWritePermissions):
            read_ok = perms.read if can_read else True
            write_ok = perms.write if can_write else True
            return read_ok and write_ok

        return [perms.repo_id for perms in self.repos if perms_ok(perms)]

    def get_repo_permissions(self, repo_id: UUID) -> RepoLogPermissions | None:
        for perms in self.repos:
            if perms.repo_id == repo_id:
                return perms
        return None

    def get_repo_readable_entities(self, repo_id: UUID) -> set[str]:
        perms = self.get_repo_permissions(repo_id)
        return (
            set(perms.readable_entities) if perms and perms.readable_entities else set()
        )


class Permissions(BaseModel):
    is_superadmin: bool | None = Field(default=None)
    logs: LogPermissions = Field(default_factory=LogPermissions)
    management: ManagementPermissions = Field(default_factory=ManagementPermissions)

    model_config = ConfigDict(extra="forbid")


ApplicableLogPermissionScope = Literal["all", "partial", "none"]


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope = Field(default="none")
    write: ApplicableLogPermissionScope = Field(default="none")

    model_config = ConfigDict(extra="forbid")


class ApplicablePermissions(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions = Field(default_factory=ApplicableLogPermissions)
    management: ManagementPermissions = Field(default_factory=ManagementPermissions)

    model_config = ConfigDict(extra="forbid")
