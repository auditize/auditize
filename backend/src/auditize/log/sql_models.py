from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint, literal_column
from sqlalchemy.orm import Mapped, column_property, mapped_column

from auditize.database.sql.models import HasId, SqlModel


class LogEntity(SqlModel, HasId):
    __tablename__ = "log_entity"

    repo_id: Mapped[UUID] = mapped_column(ForeignKey("repo.id", ondelete="CASCADE"))
    ref: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    parent_entity_id: Mapped[UUID | None] = mapped_column(ForeignKey("log_entity.id"))
    has_children: Mapped[bool] = column_property(
        literal_column(
            """
            EXISTS (
                SELECT 1
                FROM log_entity AS child_entity
                WHERE child_entity.parent_entity_id = log_entity.id
                LIMIT 1
            )
            """,
            type_=Boolean,
        )
    )
    parent_entity_ref: Mapped[str | None] = column_property(
        literal_column(
            """
            (SELECT parent_entity.ref
            FROM log_entity AS parent_entity
            WHERE parent_entity.id = log_entity.parent_entity_id)
            """,
            type_=String,
        )
    )

    __table_args__ = (UniqueConstraint("repo_id", "ref"),)
