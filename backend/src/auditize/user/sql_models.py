from datetime import datetime

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.dbm import Base
from auditize.i18n.lang import Lang
from auditize.permissions.sql_models import Permissions
from auditize.resource.sql_models import HasCreatedAt, HasId


class User(Base, HasId, HasCreatedAt):
    __tablename__ = "user"

    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    lang: Mapped[Lang] = mapped_column(default=Lang.EN)
    password_hash: Mapped[str | None] = mapped_column()
    permissions_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"))
    permissions: Mapped["Permissions"] = relationship(
        "Permissions",
        lazy="selectin",
    )
    password_reset_token: Mapped[str | None] = mapped_column()
    password_reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    authenticated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
