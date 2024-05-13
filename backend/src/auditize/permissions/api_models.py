from pydantic import BaseModel, Field

__all__ = (
    "ApplicablePermissionsData",
    "ReadWritePermissionsData",
    "ManagementPermissionsData",
    "LogPermissionsData",
    "PermissionsData",
)

from auditize.permissions.models import ApplicableLogPermissionScope


class ReadWritePermissionsData(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)


class ManagementPermissionsData(BaseModel):
    repos: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)
    users: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)
    apikeys: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)


class RepoLogPermissionsData(ReadWritePermissionsData):
    repo_id: str


class LogPermissionsData(ReadWritePermissionsData):
    repos: list[RepoLogPermissionsData] = Field(default_factory=list)


class PermissionsData(BaseModel):
    is_superadmin: bool | None = Field(default=None)
    logs: LogPermissionsData = Field(default_factory=LogPermissionsData)
    management: ManagementPermissionsData = Field(
        default_factory=ManagementPermissionsData
    )


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope = Field(default="none")
    write: ApplicableLogPermissionScope = Field(default="none")


class ApplicablePermissionsData(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions = Field(default_factory=ApplicableLogPermissions)
    management: ManagementPermissionsData = Field(
        default_factory=ManagementPermissionsData
    )
