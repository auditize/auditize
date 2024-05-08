from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

__all__ = (
    "ApplicableLogPermissions",
    "ApplicableLogPermissionScope",
    "ApplicablePermissions",
    "ReadWritePermissions",
    "ManagementPermissions",
    "LogsPermissions",
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


class LogsPermissions(ReadWritePermissions):
    repos: dict[str, ReadWritePermissions] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")

    def get_repos(self, *, can_read=False, can_write=False) -> list[str]:
        def perms_ok(perms: ReadWritePermissions):
            read_ok = perms.read if can_read else True
            write_ok = perms.write if can_write else True
            return read_ok and write_ok

        return [repo_id for repo_id, perms in self.repos.items() if perms_ok(perms)]


class Permissions(BaseModel):
    is_superadmin: bool | None = Field(default=None)
    logs: LogsPermissions = Field(default_factory=LogsPermissions)
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
