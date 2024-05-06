from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from auditize.permissions.models import Permissions


class Integration(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    name: str
    token_hash: Optional[str] = Field(default=None)
    permissions: Permissions = Field(default_factory=Permissions)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True)


class IntegrationUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[Permissions] = None
