from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

from auditize.permissions.models import Permissions


class PasswordResetToken(BaseModel):
    token: str
    expires_at: datetime


class Lang(str, Enum):
    EN = "en"
    FR = "fr"


class User(BaseModel):
    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )
    first_name: str
    last_name: str
    email: str
    lang: Lang = Field(default=Lang.EN)
    password_hash: Optional[str] = Field(default=None)
    permissions: Permissions = Field(default_factory=Permissions)
    password_reset_token: Optional[PasswordResetToken] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str = None
    lang: Lang = None
    permissions: Permissions = None
    password: str = None
