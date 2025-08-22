from typing import Any
from uuid import UUID

from sqlalchemy import ForeignKey, TypeDecorator
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.dbm import Base
from auditize.permissions.service import normalize_permissions
from auditize.permissions.sql_models import Permissions
from auditize.resource.sql_models import HasCreatedAt, HasId


class Apikey(Base, HasId, HasCreatedAt):
    __tablename__ = "apikey"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    key_hash: Mapped[str | None] = mapped_column()
    permissions_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE")
    )
    permissions: Mapped["Permissions"] = relationship(
        "Permissions",
        lazy="selectin",
    )
