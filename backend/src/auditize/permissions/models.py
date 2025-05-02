from typing import Literal, Self
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
    "ReadWritePermissionsInput",
    "ManagementPermissionsInput",
    "RepoLogPermissionsInput",
    "LogPermissionsInput",
    "PermissionsInput",
    "ReadWritePermissionsOutput",
    "ManagementPermissionsOutput",
    "RepoLogPermissionsOutput",
    "LogPermissionsOutput",
    "PermissionsOutput",
)


class ReadWritePermissions(BaseModel):
    read: bool = Field(default=False)
    write: bool = Field(default=False)

    model_config = ConfigDict(extra="forbid")

    @classmethod
    def no(cls) -> Self:
        return cls(read=False, write=False)

    @classmethod
    def yes(cls) -> Self:
        return cls(read=True, write=True)


class ManagementPermissions(BaseModel):
    repos: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    users: ReadWritePermissions = Field(default_factory=ReadWritePermissions)
    apikeys: ReadWritePermissions = Field(default_factory=ReadWritePermissions)

    model_config = ConfigDict(extra="forbid")


class RepoLogPermissions(ReadWritePermissions):
    repo_id: UUID
    readable_entities: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class LogPermissions(ReadWritePermissions):
    repos: list[RepoLogPermissions] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    def get_repos(self, *, can_read=False, can_write=False) -> list[UUID]:
        def perms_ok(perms: RepoLogPermissions):
            read_ok = perms.read or perms.readable_entities if can_read else True
            write_ok = perms.write if can_write else True
            return read_ok and write_ok

        return [perms.repo_id for perms in self.repos if perms_ok(perms)]

    def get_repo_permissions(self, repo_id: UUID) -> RepoLogPermissions:
        for perms in self.repos:
            if perms.repo_id == repo_id:
                return perms
        return RepoLogPermissions(
            repo_id=repo_id, read=False, write=False, readable_entities=list()
        )

    def get_repo_readable_entities(self, repo_id: UUID) -> set[str]:
        perms = self.get_repo_permissions(repo_id)
        return set(perms.readable_entities) if perms.readable_entities else set()


class Permissions(BaseModel):
    is_superadmin: bool = Field(default=False)
    logs: LogPermissions = Field(default_factory=LogPermissions)
    management: ManagementPermissions = Field(default_factory=ManagementPermissions)

    model_config = ConfigDict(extra="forbid")


def _RepoLogPermissionsField(**kwargs):  # noqa
    return Field(
        description="Per repository permissions",
        **kwargs,
    )


def _IsSuperadminField(**kwargs):  # noqa
    return Field(
        description="Superadmin has all permissions",
        **kwargs,
    )


def _ManagementPermissionsField(**kwargs):  # noqa
    return Field(
        description="Management permissions",
        **kwargs,
    )


def _LogPermissionsField(**kwargs):  # noqa
    return Field(
        description="Log permissions",
        **kwargs,
    )


_PERMISSIONS_EXAMPLE = {
    "example": {
        "is_superadmin": False,
        "logs": {
            "read": True,
            "write": False,
            "repos": [
                {
                    "repo_id": "DCFB6049-3BB7-49C5-94A9-64FC9226AE30",
                    "read": False,
                    "write": False,
                },
                {
                    "repo_id": "E3D38457-670B-42EE-AF1B-10FA90597E68",
                    "read": False,
                    "write": True,
                },
            ],
        },
        "management": {
            "repos": {"read": True, "write": False},
            "users": {"read": True, "write": True},
            "apikeys": {"read": False, "write": False},
        },
    }
}


class ReadWritePermissionsInput(BaseModel):
    read: bool | None = Field(default=None)
    write: bool | None = Field(default=None)

    @classmethod
    def no(cls) -> Self:
        return cls(read=False, write=False)

    @classmethod
    def yes(cls) -> Self:
        return cls(read=True, write=True)


class ManagementPermissionsInput(BaseModel):
    repos: ReadWritePermissionsInput = Field(default_factory=ReadWritePermissionsInput)
    users: ReadWritePermissionsInput = Field(default_factory=ReadWritePermissionsInput)
    apikeys: ReadWritePermissionsInput = Field(
        default_factory=ReadWritePermissionsInput
    )


class RepoLogPermissionsInput(ReadWritePermissionsInput):
    repo_id: UUID
    readable_entities: list[str] | None = Field(default=None)


class LogPermissionsInput(ReadWritePermissionsInput):
    repos: list[RepoLogPermissionsInput] = Field(default_factory=list)


class PermissionsInput(BaseModel):
    is_superadmin: bool | None = _IsSuperadminField(default=None)
    logs: LogPermissionsInput = _LogPermissionsField(
        default_factory=LogPermissionsInput
    )
    management: ManagementPermissionsInput = _ManagementPermissionsField(
        default_factory=ManagementPermissionsInput
    )

    model_config = ConfigDict(json_schema_extra={"example": _PERMISSIONS_EXAMPLE})


class ReadWritePermissionsOutput(BaseModel):
    read: bool = Field()
    write: bool = Field()


class ManagementPermissionsOutput(BaseModel):
    repos: ReadWritePermissionsOutput = Field(
        default_factory=ReadWritePermissionsOutput
    )
    users: ReadWritePermissionsOutput = Field(
        default_factory=ReadWritePermissionsOutput
    )
    apikeys: ReadWritePermissionsOutput = Field(
        default_factory=ReadWritePermissionsOutput
    )


class RepoLogPermissionsOutput(ReadWritePermissionsOutput):
    repo_id: UUID
    readable_entities: list[str]


class LogPermissionsOutput(ReadWritePermissionsOutput):
    repos: list[RepoLogPermissionsOutput] = Field()


class PermissionsOutput(BaseModel):
    is_superadmin: bool = _IsSuperadminField()
    logs: LogPermissions = _LogPermissionsField()
    management: ManagementPermissionsOutput = _ManagementPermissionsField()

    model_config = ConfigDict(json_schema_extra={"example": _PERMISSIONS_EXAMPLE})


ApplicableLogPermissionScope = Literal["all", "partial", "none"]


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope = Field(default="none")
    write: ApplicableLogPermissionScope = Field(default="none")


class ApplicablePermissions(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions = Field(default_factory=ApplicableLogPermissions)
    management: ManagementPermissions = Field(default_factory=ManagementPermissions)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_superadmin": False,
                "logs": {
                    "read": "all",
                    "write": "partial",
                },
                "management": {
                    "repos": {"read": True, "write": False},
                    "users": {"read": True, "write": True},
                    "apikeys": {"read": False, "write": False},
                },
            }
        }
    )
