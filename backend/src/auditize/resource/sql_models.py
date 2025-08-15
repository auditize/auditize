import uuid

from sqlalchemy import DateTime, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from auditize.helpers.datetime import now


class HasId:
    id: Mapped[Uuid] = mapped_column(Uuid(), primary_key=True, default=uuid.uuid4)


class HasCreatedAt:
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=now
    )
