from sqlalchemy.orm import Mapped, mapped_column

from auditize.database.dbm import SqlModel
from auditize.database.sql.models import HasDates, HasId
from auditize.permissions.sql_models import HasPermissions


class Apikey(SqlModel, HasId, HasDates, HasPermissions):
    __tablename__ = "apikey"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    key_hash: Mapped[str | None] = mapped_column()
