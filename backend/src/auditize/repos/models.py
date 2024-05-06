from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field


class Repo(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True)


class RepoUpdate(BaseModel):
    name: Optional[str] = None


class RepoStats(BaseModel):
    first_log_date: Optional[datetime] = None
    last_log_date: Optional[datetime] = None
    log_count: int = 0
    storage_size: int = 0
