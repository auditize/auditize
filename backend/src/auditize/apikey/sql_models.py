from sqlalchemy.orm import Mapped, mapped_column

from auditize.database.dbm import Base
from auditize.permissions.sql_models import HasPermissions
from auditize.resource.sql_models import HasCreatedAt, HasId


class Apikey(Base, HasId, HasCreatedAt, HasPermissions):
    __tablename__ = "apikey"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    key_hash: Mapped[str | None] = mapped_column()
