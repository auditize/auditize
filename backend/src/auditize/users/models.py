from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from auditize.permissions.models import Permissions
from auditize.resource.models import HasCreatedAt, HasId


class PasswordResetToken(BaseModel):
    token: str
    expires_at: datetime


class Lang(str, Enum):
    EN = "en"
    FR = "fr"


class User(BaseModel, HasId, HasCreatedAt):
    first_name: str
    last_name: str
    email: str
    lang: Lang = Field(default=Lang.EN)
    password_hash: Optional[str] = Field(default=None)
    permissions: Permissions = Field(default_factory=Permissions)
    password_reset_token: Optional[PasswordResetToken] = Field(default=None)


class UserUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str = None
    lang: Lang = None
    permissions: Permissions = None
    password: str = None
