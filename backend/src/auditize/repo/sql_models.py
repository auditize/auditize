import enum
from uuid import UUID

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.sql.models import HasDates, HasId, SqlModel


class RepoStatus(enum.StrEnum):
    ENABLED = "enabled"
    READONLY = "readonly"
    DISABLED = "disabled"


class Repo(SqlModel, HasId, HasDates):
    from auditize.log_i18n_profile.sql_models import LogI18nProfile

    __tablename__ = "repo"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    log_db_name: Mapped[str] = mapped_column(unique=True)
    status: Mapped[RepoStatus] = mapped_column(
        SqlEnum(RepoStatus, native_enum=False), default=RepoStatus.ENABLED
    )
    retention_period: Mapped[int | None] = mapped_column()
    log_i18n_profile_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("log_i18n_profile.id")
    )
    log_i18n_profile: Mapped[LogI18nProfile | None] = relationship(
        "LogI18nProfile", lazy="selectin"
    )
    reindex_cursor: Mapped[str | None] = mapped_column(default=None)
    reindexed_logs_count: Mapped[int] = mapped_column(default=0)
