from pydantic import BaseModel, Field


__all__ = (
    "ReadWritePermissions",
    "EntitiesPermissions",
    "LogsPermissions",
    "Permissions"
)


class ReadWritePermissions(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)

    @classmethod
    def no(cls) -> "ReadWritePermissions":
        return cls(read=False, write=False)


class EntitiesPermissions(BaseModel):
    repos: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    users: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    integrations: ReadWritePermissions = Field(default_factory=ReadWritePermissions)


class LogsPermissions(ReadWritePermissions):
    repos: dict[str, ReadWritePermissions] = Field(default_factory=dict)


class Permissions(BaseModel):
    is_superadmin: bool | None = Field(default=None)
    logs: LogsPermissions = Field(default_factory=LogsPermissions)
    entities: EntitiesPermissions = Field(default_factory=EntitiesPermissions)
