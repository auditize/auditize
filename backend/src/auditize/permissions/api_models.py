from pydantic import BaseModel, Field

__all__ = (
    "ReadWritePermissionsData",
    "ManagementPermissionsData",
    "LogsPermissionsData",
    "PermissionsData",
)

from auditize.permissions.models import ApplicableLogPermissionScope


class ReadWritePermissionsData(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)


class ManagementPermissionsData(BaseModel):
    repos: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)
    users: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)
    integrations: ReadWritePermissionsData = Field(
        default_factory=ReadWritePermissionsData
    )


class LogsPermissionsData(ReadWritePermissionsData):
    repos: dict[str, ReadWritePermissionsData] = Field(default_factory=dict)


class PermissionsData(BaseModel):
    is_superadmin: bool | None = Field(default=None)
    logs: LogsPermissionsData = Field(default_factory=LogsPermissionsData)
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
