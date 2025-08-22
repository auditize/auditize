from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.dbm import Base
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
