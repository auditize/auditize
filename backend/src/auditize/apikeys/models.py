from typing import Optional

from pydantic import BaseModel, Field

from auditize.permissions.models import Permissions
from auditize.resource.models import HasCreatedAt, HasUuid


class Apikey(BaseModel, HasUuid, HasCreatedAt):
    name: str
    key_hash: Optional[str] = Field(default=None)
    permissions: Permissions = Field(default_factory=Permissions)


class ApikeyUpdate(BaseModel):
    name: str = None
    permissions: Permissions = None
