from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    MappedAsDataclass,
    declared_attr,
    mapped_column,
    relationship,
)

from auditize.database.sql.models import SqlModel


class ReadableLogEntityPermission(SqlModel):
    __tablename__ = "permissions_readable_log_entity"

    id: Mapped[int] = mapped_column(primary_key=True)
    # NB: since a log entity can appear and disappear depending on log expiration,
    # we don't want to make a foreign key to the log entity table but rather
    # a lazy relationship
    ref: Mapped[str] = mapped_column()
    repo_log_permissions_id: Mapped[int] = mapped_column(
        ForeignKey("permissions_repo_log.id", ondelete="CASCADE")
    )


class RepoLogPermissions(MappedAsDataclass, SqlModel):
    __tablename__ = "permissions_repo_log"

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


class Permissions(MappedAsDataclass, SqlModel):
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
        lazy="selectin", cascade="all, delete-orphan", default_factory=list
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


class HasPermissions:
    @declared_attr
    def permissions_id(self) -> Mapped[int]:
        return mapped_column(ForeignKey("permissions.id"))

    @declared_attr
    def permissions(self) -> Mapped[Permissions]:
        return relationship("Permissions", lazy="selectin")
