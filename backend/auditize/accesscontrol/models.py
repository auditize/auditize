from pydantic import BaseModel, Field


class ReadWritePermissions(BaseModel):
    read: bool = Field(default=False)
    write: bool = Field(default=False)


class EntitiesRights(BaseModel):
    repos: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    users: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    integrations: ReadWritePermissions = Field(default_factory=ReadWritePermissions)


class LogsRights(ReadWritePermissions):
    repos: dict[str, ReadWritePermissions] = Field(default_factory=dict)


class AccessRights(BaseModel):
    is_superadmin: bool = False
    logs: LogsRights = Field(default_factory=LogsRights)
    entities: EntitiesRights = Field(default_factory=EntitiesRights)
