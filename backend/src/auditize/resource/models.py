from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from pydantic import Field


class HasId:
    id: Optional[UUID] = Field(default=None, alias="_id")


class HasCreatedAt:
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
