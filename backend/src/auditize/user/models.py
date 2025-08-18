from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import DateTime, TypeDecorator
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from auditize.database.dbm import Base
from auditize.i18n.lang import Lang
from auditize.permissions.models import (
    ApplicablePermissions,
    Permissions,
    PermissionsInput,
    PermissionsOutput,
)
from auditize.permissions.operations import (
    compute_applicable_permissions,
    normalize_permissions,
)
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse
from auditize.resource.sql_models import HasCreatedAt, HasId

USER_PASSWORD_MIN_LENGTH = 8


class PermissionsAsJSON(TypeDecorator):
    impl = JSON

    def process_bind_param(self, value: Permissions | Any, _):
        return (
            normalize_permissions(value).model_dump(mode="json")
            if isinstance(value, Permissions)
            else value
        )

    def process_result_value(self, value: dict, _) -> Permissions:
        return Permissions.model_validate(value)


class User(Base, HasId, HasCreatedAt):
    __tablename__ = "user"

    first_name: Mapped[str] = mapped_column(nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(nullable=False, index=True)
    email: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    lang: Mapped[Lang] = mapped_column(nullable=False, default=Lang.EN)
    password_hash: Mapped[str | None] = mapped_column(nullable=True)
    permissions: Mapped[Permissions] = mapped_column(
        PermissionsAsJSON(), nullable=False
    )
    password_reset_token: Mapped[str | None] = mapped_column(nullable=True)
    password_reset_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    authenticated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


def _UserFirstNameField(**kwargs):  # noqa
    return Field(
        description="The user first name",
        json_schema_extra={
            "example": "John",
        },
        **kwargs,
    )


def _UserLastNameField(**kwargs):  # noqa
    return Field(
        description="The user last name",
        json_schema_extra={
            "example": "Doe",
        },
        **kwargs,
    )


def _UserEmailField(**kwargs):  # noqa
    return Field(
        description="The user email",
        json_schema_extra={"example": "john.doe@example.net"},
        **kwargs,
    )


def _UserLangField(default: Lang | None = Lang.EN, **kwargs):  # noqa
    return Field(
        description="The user language",
        default=default,
        json_schema_extra={"example": "en"},
        **kwargs,
    )


def _UserPasswordField(**kwargs):  # noqa
    min_length = kwargs.pop("min_length", USER_PASSWORD_MIN_LENGTH)
    return Field(
        description="The user password",
        min_length=min_length,
        json_schema_extra={"example": "some very highly secret password"},
        **kwargs,
    )


def _UserIdField():  # noqa
    return IdField(description="User ID")


def _UserPermissionsField(**kwargs):  # noqa
    return Field(
        description="The user permissions",
        **kwargs,
    )


def _UserAuthenticatedAtField(**kwargs):  # noqa
    return Field(
        description="The date at which the user authenticated for the last time",
        **kwargs,
    )


class UserCreate(BaseModel):
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: EmailStr = _UserEmailField()
    lang: Lang = _UserLangField()
    permissions: PermissionsInput = _UserPermissionsField(
        default_factory=PermissionsInput
    )


class _UserUpdate(BaseModel):
    # NB: we don't implement a simple `UserUpdate` class here, because we don't want to
    # allow a password update in PATCH /users/{user_id} endpoint.

    first_name: str = _UserFirstNameField(default=None)
    last_name: str = _UserLastNameField(default=None)
    email: str = _UserEmailField(default=None)
    lang: Lang = _UserLangField(default=None)
    permissions: PermissionsInput = _UserPermissionsField(default=None)


class UserUpdate(_UserUpdate):
    password: str = None


class UserUpdateRequest(_UserUpdate):
    pass


class UserCreationResponse(BaseModel):
    id: UUID = _UserIdField()


class UserResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _UserIdField()
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()
    lang: Lang = _UserLangField()
    permissions: PermissionsOutput = _UserPermissionsField()
    authenticated_at: datetime | None = _UserAuthenticatedAtField()


class UserListResponse(PagePaginatedResponse[User, UserResponse]):
    @classmethod
    def build_item(cls, user: User) -> UserResponse:
        return UserResponse.model_validate(user, from_attributes=True)


class UserPasswordResetInfoResponse(BaseModel):
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()


class UserPasswordResetRequest(BaseModel):
    password: str = _UserPasswordField()


class UserAuthenticationRequest(BaseModel):
    email: str = _UserEmailField()
    # NB: there is no minimal length for the password here as the constraints
    # apply when the user choose his password, not when he uses it
    password: str = _UserPasswordField(min_length=None)


class UserMeResponse(BaseModel):
    id: UUID = _UserIdField()
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()
    lang: Lang = _UserLangField()
    permissions: ApplicablePermissions = _UserPermissionsField()

    model_config = ConfigDict(from_attributes=True)

    @field_validator("permissions", mode="before")
    def validate_permissions(cls, permissions: Permissions):
        return compute_applicable_permissions(permissions)

    @classmethod
    def from_user(cls, user: User):
        return cls.model_validate(user)


class UserMeUpdateRequest(BaseModel):
    lang: Lang = _UserLangField(default=None)
    password: str = _UserPasswordField(default=None)


# NB: yes, the request of a request...
class UserPasswordResetRequestRequest(BaseModel):
    email: str = _UserEmailField()
