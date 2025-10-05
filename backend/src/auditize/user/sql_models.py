from datetime import datetime

from sqlalchemy import DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column

from auditize.database.sql.models import HasDates, HasId, SqlModel
from auditize.i18n.lang import Lang
from auditize.permissions.sql_models import HasPermissions


class User(SqlModel, HasId, HasDates, HasPermissions):
    __tablename__ = "user"

    first_name: Mapped[str] = mapped_column(index=True)
    last_name: Mapped[str] = mapped_column(index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    lang: Mapped[Lang] = mapped_column(Enum(Lang, native_enum=False), default=Lang.EN)
    password_hash: Mapped[str | None] = mapped_column()
    password_reset_token: Mapped[str | None] = mapped_column()
    password_reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    authenticated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
