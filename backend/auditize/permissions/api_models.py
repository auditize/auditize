from pydantic import BaseModel, Field


__all__ = (
    "ReadWritePermissionsData",
    "EntitiesPermissionsData",
    "LogsPermissionsData",
    "PermissionsData"
)


class ReadWritePermissionsData(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)


class EntitiesPermissionsData(BaseModel):
    repos: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)
    users: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)
    integrations: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)


class LogsPermissionsData(ReadWritePermissionsData):
    repos: dict[str, ReadWritePermissionsData] = Field(default_factory=dict)


class PermissionsData(BaseModel):
    is_superadmin: bool | None = Field(default=None)
    logs: LogsPermissionsData = Field(default_factory=LogsPermissionsData)
    entities: EntitiesPermissionsData = Field(default_factory=EntitiesPermissionsData)


class ApplicablePermissionsData(BaseModel):
    is_superadmin: bool
    logs: ReadWritePermissionsData = Field(default_factory=ReadWritePermissionsData)
    entities: EntitiesPermissionsData = Field(default_factory=EntitiesPermissionsData)
