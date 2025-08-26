from uuid import UUID, uuid4

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column


class HasId:
    id: Mapped[UUID] = mapped_column(Uuid(), primary_key=True, default=uuid4)


class HasCreatedAt:
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class HasUpdatedAt:
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class HasDates(HasCreatedAt, HasUpdatedAt):
    pass
