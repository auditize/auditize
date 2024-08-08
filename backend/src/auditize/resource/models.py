from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BeforeValidator, Field


class HasId:
    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )


class HasUuid:
    id: Optional[UUID] = Field(default=None, alias="_id")


class HasCreatedAt:
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
