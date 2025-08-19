from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column, relationship

from auditize.database.dbm import Base

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


class ReadableLogEntityPermission(Base):
    __tablename__ = "readable_log_entity_permission"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NB: since a log entity can appear and disappear depending on log expiration,
    # we don't want to make a foreign key to the log entity table but rather
    # a lazy relationship
    ref: Mapped[str] = mapped_column()
    repo_log_permissions_id: Mapped[int] = mapped_column(
        ForeignKey("repo_log_permissions.id", ondelete="CASCADE")
    )


class RepoLogPermissions(MappedAsDataclass, Base):
    __tablename__ = "repo_log_permissions"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    repo_id: Mapped[UUID] = mapped_column(ForeignKey("repo.id", ondelete="CASCADE"))
    read: Mapped[bool] = mapped_column(default=False)
    write: Mapped[bool] = mapped_column(default=False)
    readable_entities: Mapped[list[ReadableLogEntityPermission]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", default_factory=list
    )
    permissions_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), init=False
    )


class Permissions(MappedAsDataclass, Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    is_superadmin: Mapped[bool] = mapped_column(default=False)
    repos_read: Mapped[bool] = mapped_column(default=False)
    repos_write: Mapped[bool] = mapped_column(default=False)
    users_read: Mapped[bool] = mapped_column(default=False)
    users_write: Mapped[bool] = mapped_column(default=False)
    apikeys_read: Mapped[bool] = mapped_column(default=False)
    apikeys_write: Mapped[bool] = mapped_column(default=False)
    logs_read: Mapped[bool] = mapped_column(default=False)
    logs_write: Mapped[bool] = mapped_column(default=False)

    repo_log_permissions: Mapped[list[RepoLogPermissions]] = relationship(
        lazy="selectin", default_factory=list
    )

    def get_repo_log_permissions_by_id(
        self, repo_id: UUID
    ) -> RepoLogPermissions | None:
        for repo_perms in self.repo_log_permissions:
            if repo_perms.repo_id == repo_id:
                return repo_perms
        return None

    def get_repo_readable_entities(self, repo_id: UUID) -> set[str]:
        perms = self.get_repo_log_permissions_by_id(repo_id)
        return set(entity.ref for entity in perms.readable_entities) if perms else set()


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

    @classmethod
    def yes(cls) -> Self:
        return cls(read=True, write=True)

    @classmethod
    def no(cls) -> Self:
        return cls(read=False, write=False)


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
    logs: LogPermissionsOutput = _LogPermissionsField()
    management: ManagementPermissionsOutput = _ManagementPermissionsField()

    model_config = ConfigDict(json_schema_extra={"example": _PERMISSIONS_EXAMPLE})


ApplicableLogPermissionScope = Literal["all", "partial", "none"]


class ApplicableLogPermissions(BaseModel):
    read: ApplicableLogPermissionScope = Field(default="none")
    write: ApplicableLogPermissionScope = Field(default="none")


class ApplicablePermissions(BaseModel):
    is_superadmin: bool
    logs: ApplicableLogPermissions = Field(default_factory=ApplicableLogPermissions)
    management: ManagementPermissionsOutput = Field(
        default_factory=ManagementPermissionsOutput
    )

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
