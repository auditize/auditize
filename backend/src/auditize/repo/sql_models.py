from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

if TYPE_CHECKING:
    from auditize.log_i18n_profile.sql_models import LogI18nProfile

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.dbm import Base
from auditize.resource.sql_models import HasCreatedAt, HasId


class RepoStatus(str, Enum):
    enabled = "enabled"
    readonly = "readonly"
    disabled = "disabled"


class Repo(Base, HasId, HasCreatedAt):
    __tablename__ = "repo"

    name: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    log_db_name: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[RepoStatus] = mapped_column(
        nullable=False, default=RepoStatus.enabled
    )
    retention_period: Mapped[Optional[int]] = mapped_column(nullable=True)
    log_i18n_profile_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("log_i18n_profile.id"), nullable=True
    )
    log_i18n_profile: Mapped[Optional["LogI18nProfile"]] = relationship(
        "LogI18nProfile", lazy="selectin"
    )
