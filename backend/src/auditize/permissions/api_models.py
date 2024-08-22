from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    repo_id: UUID
    readable_entities: list[str] | None = Field(default=None)


class RepoLogPermissionsOutputData(ReadWritePermissionsOutputData):
    repo_id: UUID
    readable_entities: list[str]


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_superadmin": False,
                "logs": {
                    "read": True,
                    "write": False,
                    "repos": [
                        {
                            "repo_id": "DCFB6049-3BB7-49C5-94A9-64FC9226AE30",
                            "read": True,
                        },
                        {
                            "repo_id": "E3D38457-670B-42EE-AF1B-10FA90597E68",
                            "read": True,
                            "write": True,
                        },
                    ],
                },
                "management": {
                    "repos": {"read": True, "write": False},
                    "users": {"read": True, "write": True},
                },
            }
        }
    )


class PermissionsOutputData(BaseModel):
    is_superadmin: bool = Field(description="Superadmin has all permissions")
    logs: LogPermissionsOutputData = Field(description="Log permissions")
    management: ManagementPermissionsOutputData = Field(
        description="Management permissions"
    )

    model_config = ConfigDict(
        json_schema_extra={
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
    )


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope = Field()
    write: ApplicableLogPermissionScope = Field()


class ApplicablePermissionsData(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions = Field(...)
    management: ManagementPermissionsOutputData = Field(...)

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
