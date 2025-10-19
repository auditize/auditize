from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from auditize.permissions.sql_models import (
    Permissions,
    RepoLogPermissions,
)

__all__ = (
    "ApplicableLogPermissions",
    "ApplicableLogPermissionScope",
    "ApplicablePermissions",
    "RepoLogPermissions",
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

    @classmethod
    def yes(cls) -> Self:
        return cls(read=True, write=True)

    @classmethod
    def no(cls) -> Self:
        return cls(read=False, write=False)


class ManagementPermissionsOutput(BaseModel):
    repos: ReadWritePermissionsOutput
    users: ReadWritePermissionsOutput
    apikeys: ReadWritePermissionsOutput


class RepoLogPermissionsOutput(ReadWritePermissionsOutput):
    repo_id: UUID
    readable_entities: list[str]


class LogPermissionsOutput(ReadWritePermissionsOutput):
    repos: list[RepoLogPermissionsOutput] = Field()


class PermissionsOutput(BaseModel):
    is_superadmin: bool = _IsSuperadminField()
    logs: LogPermissionsOutput = _LogPermissionsField()
    management: ManagementPermissionsOutput = _ManagementPermissionsField()

    model_config = ConfigDict(json_schema_extra={"example": _PERMISSIONS_EXAMPLE})


ApplicableLogPermissionScope = Literal["all", "partial", "none"]


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope
    write: ApplicableLogPermissionScope


class ApplicablePermissions(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions
    management: ManagementPermissionsOutput

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
