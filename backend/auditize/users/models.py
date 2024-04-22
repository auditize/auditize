from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field, ConfigDict
from bson import ObjectId


class User(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    first_name: str
    last_name: str
    email: str
    password_hash: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
