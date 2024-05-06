from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field

from auditize.permissions.models import Permissions


class SignupToken(BaseModel):
    token: str
    expires_at: datetime


class User(BaseModel):
    id: Optional[ObjectId] = Field(default=None, alias="_id")
    first_name: str
    last_name: str
    email: str
    password_hash: Optional[str] = Field(default=None)
    permissions: Permissions = Field(default_factory=Permissions)
    signup_token: Optional[SignupToken] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(arbitrary_types_allowed=True)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    permissions: Optional[Permissions] = None
