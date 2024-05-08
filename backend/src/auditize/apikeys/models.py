from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

from auditize.permissions.models import Permissions


class Apikey(BaseModel):
    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )
    name: str
    token_hash: Optional[str] = Field(default=None)
    permissions: Permissions = Field(default_factory=Permissions)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApikeyUpdate(BaseModel):
    name: Optional[str] = None
    permissions: Optional[Permissions] = None
