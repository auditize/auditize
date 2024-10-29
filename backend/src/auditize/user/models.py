from datetime import datetime

from pydantic import BaseModel, Field

from auditize.i18n.lang import Lang
from auditize.permissions.models import Permissions
from auditize.resource.models import HasCreatedAt, HasId

USER_PASSWORD_MIN_LENGTH = 8


class PasswordResetToken(BaseModel):
    token: str
    expires_at: datetime


class User(BaseModel, HasId, HasCreatedAt):
    first_name: str
    last_name: str
    email: str
    lang: Lang = Lang.EN
    password_hash: str | None = None
    permissions: Permissions = Field(default_factory=Permissions)
    password_reset_token: PasswordResetToken | None = None
    authenticated_at: datetime | None = None


class UserUpdate(BaseModel):
    first_name: str = None
    last_name: str = None
    email: str = None
    lang: Lang = None
    permissions: Permissions = None
    password: str = None
