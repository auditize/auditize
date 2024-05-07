from pydantic import BaseModel, Field

__all__ = (
    "ReadWritePermissionsData",
    "EntitiesPermissionsData",
    "LogsPermissionsData",
    "PermissionsData",
)

from auditize.permissions.models import ApplicableLogPermissionScope


class ReadWritePermissionsData(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)


class EntitiesPermissionsData(BaseModel):
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
    entities: EntitiesPermissionsData = Field(default_factory=EntitiesPermissionsData)


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope = Field(default="none")
    write: ApplicableLogPermissionScope = Field(default="none")


class ApplicablePermissionsData(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions = Field(default_factory=ApplicableLogPermissions)
    entities: EntitiesPermissionsData = Field(default_factory=EntitiesPermissionsData)
