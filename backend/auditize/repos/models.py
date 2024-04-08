from typing import Optional
from datetime import datetime, timezone
from bson import ObjectId

from pydantic import BaseModel, Field, ConfigDict


class Repo(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
