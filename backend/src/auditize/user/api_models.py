from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from auditize.i18n.lang import Lang
from auditize.permissions.api_models import (
    ApplicablePermissionsData,
    PermissionsInputData,
    PermissionsOutputData,
)
from auditize.permissions.operations import compute_applicable_permissions
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse
from auditize.user.models import USER_PASSWORD_MIN_LENGTH, User


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


class UserCreationRequest(BaseModel):
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: EmailStr = _UserEmailField()
    lang: Lang = _UserLangField()
    permissions: PermissionsInputData = _UserPermissionsField(
        default_factory=PermissionsInputData
    )


class UserUpdateRequest(BaseModel):
    first_name: str = _UserFirstNameField(default=None)
    last_name: str = _UserLastNameField(default=None)
    email: str = _UserEmailField(default=None)
    lang: Lang = _UserLangField(default=None)
    permissions: PermissionsInputData = _UserPermissionsField(default=None)


class UserCreationResponse(BaseModel):
    id: UUID = _UserIdField()


class UserReadingResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _UserIdField()
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()
    lang: Lang = _UserLangField()
    permissions: PermissionsOutputData = _UserPermissionsField()
    authenticated_at: datetime | None = _UserAuthenticatedAtField()


class UserListResponse(PagePaginatedResponse[User, UserReadingResponse]):
    @classmethod
    def build_item(cls, user: User) -> UserReadingResponse:
        return UserReadingResponse.model_validate(user.model_dump())


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
    permissions: ApplicablePermissionsData = _UserPermissionsField()

    @classmethod
    def from_user(cls, user: User):
        return cls.model_validate(
            {
                **user.model_dump(exclude={"permissions"}),
                "permissions": compute_applicable_permissions(
                    user.permissions
                ).model_dump(),
            }
        )


class UserMeUpdateRequest(BaseModel):
    lang: Lang = _UserLangField(default=None)
    password: str = _UserPasswordField(default=None)


# NB: yes, the request of a request...
class UserPasswordResetRequestRequest(BaseModel):
    email: str = _UserEmailField()
