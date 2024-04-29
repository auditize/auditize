from pydantic import BaseModel, Field


class ReadWritePermissions(BaseModel):
    read: bool = Field(default=False)
    write: bool = Field(default=False)


class ManageableEntities(BaseModel):
    repos: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    users: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    integrations: ReadWritePermissions = Field(default_factory=ReadWritePermissions)


class LogPermissions(ReadWritePermissions):
    repos: dict[str, ReadWritePermissions] = Field(default_factory=dict)


class AccessRights(BaseModel):
    is_superadmin: bool = False
    logs: LogPermissions = Field(default_factory=LogPermissions)
    entities: ManageableEntities = Field(default_factory=ManageableEntities)
