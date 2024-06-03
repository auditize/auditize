from pydantic import BaseModel, Field

__all__ = (
    "ApplicablePermissionsData",
    "ReadWritePermissionsInputData",
    "ReadWritePermissionsOutputData",
    "ManagementPermissionsInputData",
    "ManagementPermissionsOutputData",
    "LogPermissionsInputData",
    "LogPermissionsOutputData",
    "PermissionsInputData",
    "PermissionsOutputData",
)

from auditize.permissions.models import ApplicableLogPermissionScope


class ReadWritePermissionsInputData(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)


class ReadWritePermissionsOutputData(BaseModel):
    read: bool
    write: bool


class ManagementPermissionsInputData(BaseModel):
    repos: ReadWritePermissionsInputData = Field(
        default_factory=ReadWritePermissionsInputData
    )
    users: ReadWritePermissionsInputData = Field(
        default_factory=ReadWritePermissionsInputData
    )
    apikeys: ReadWritePermissionsInputData = Field(
        default_factory=ReadWritePermissionsInputData
    )


class ManagementPermissionsOutputData(BaseModel):
    repos: ReadWritePermissionsOutputData
    users: ReadWritePermissionsOutputData
    apikeys: ReadWritePermissionsOutputData


class RepoLogPermissionsInputData(ReadWritePermissionsInputData):
    repo_id: str


class RepoLogPermissionsOutputData(ReadWritePermissionsOutputData):
    repo_id: str


class LogPermissionsInputData(ReadWritePermissionsInputData):
    repos: list[RepoLogPermissionsInputData] = Field(
        description="Per repository permissions", default_factory=list
    )


class LogPermissionsOutputData(ReadWritePermissionsOutputData):
    repos: list[RepoLogPermissionsOutputData] = Field(
        description="Per repository permissions"
    )


class PermissionsInputData(BaseModel):
    is_superadmin: bool | None = Field(
        description="Superadmin has all permissions", default=None
    )
    logs: LogPermissionsInputData = Field(
        description="Log permissions", default_factory=LogPermissionsInputData
    )
    management: ManagementPermissionsInputData = Field(
        description="Management permissions",
        default_factory=ManagementPermissionsInputData,
    )


class PermissionsOutputData(BaseModel):
    is_superadmin: bool = Field(description="Superadmin has all permissions")
    logs: LogPermissionsOutputData = Field(description="Log permissions")
    management: ManagementPermissionsOutputData = Field(
        description="Management permissions"
    )


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope = Field()
    write: ApplicableLogPermissionScope = Field()


class ApplicablePermissionsData(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions = Field(...)
    management: ManagementPermissionsOutputData = Field(...)
