from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class Integration(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    token_hash: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
