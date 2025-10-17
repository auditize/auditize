from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from auditize.api.models.common import IdField
from auditize.api.models.dates import (
    CreatedAtField,
    HasDatetimeSerialization,
    UpdatedAtField,
)
from auditize.api.models.page_pagination import PagePaginatedResponse
from auditize.i18n.lang import Lang
from auditize.permissions.models import (
    ApplicablePermissions,
    Permissions,
    PermissionsInput,
    PermissionsOutput,
)
from auditize.permissions.service import (
    build_permissions_output,
    compute_applicable_permissions,
)
from auditize.user.sql_models import User

USER_PASSWORD_MIN_LENGTH = 8


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


def _UserLangField(**kwargs):  # noqa
    return Field(
        description="The user language",
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
    lang: Lang = _UserLangField(default=Lang.EN)
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


class UserResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _UserIdField()
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()
    lang: Lang = _UserLangField()
    permissions: PermissionsOutput = _UserPermissionsField()
    authenticated_at: datetime | None = _UserAuthenticatedAtField()

    @field_validator("permissions", mode="before")
    def validate_permissions(cls, permissions: Permissions):
        return build_permissions_output(permissions)


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
