from enum import Enum
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.dbm import SqlModel
from auditize.database.sql.models import HasDates, HasId


class RepoStatus(str, Enum):
    enabled = "enabled"
    readonly = "readonly"
    disabled = "disabled"


class Repo(SqlModel, HasId, HasDates):
    from auditize.log_i18n_profile.sql_models import LogI18nProfile

    __tablename__ = "repo"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    log_db_name: Mapped[str] = mapped_column(unique=True)
    status: Mapped[RepoStatus] = mapped_column(String(), default=RepoStatus.enabled)
    retention_period: Mapped[int | None] = mapped_column()
    log_i18n_profile_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("log_i18n_profile.id")
    )
    log_i18n_profile: Mapped[LogI18nProfile | None] = relationship(
        "LogI18nProfile", lazy="selectin"
    )
