from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from auditize.helpers.pagination.page.api_models import PagePaginatedResponse
from auditize.permissions.api_models import (
    ApplicablePermissionsData,
    PermissionsInputData,
    PermissionsOutputData,
)
from auditize.permissions.operations import compute_applicable_permissions
from auditize.users.models import Lang, User


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
    return Field(
        description="The user password",
        json_schema_extra={"example": "some very highly secret password"},
        **kwargs,
    )


def _UserIdField():  # noqa
    return Field(
        description="The user ID",
        json_schema_extra={"example": "FEC4A4E6-AC13-455F-A0F8-E71AA0C37B7D"},
    )


def _UserPermissionsField(**kwargs):  # noqa
    return Field(
        description="The user permissions",
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

    def to_db_model(self):
        return User.model_validate(self.model_dump())


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = _UserFirstNameField(default=None)
    last_name: Optional[str] = _UserLastNameField(default=None)
    email: Optional[str] = _UserEmailField(default=None)
    lang: Optional[Lang] = _UserLangField(default=None)
    permissions: Optional[PermissionsInputData] = _UserPermissionsField(default=None)


class UserCreationResponse(BaseModel):
    id: str = _UserIdField()


class UserReadingResponse(BaseModel):
    id: str = _UserIdField()
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()
    lang: Lang = _UserLangField()
    permissions: PermissionsOutputData = _UserPermissionsField()

    @classmethod
    def from_db_model(cls, user: User):
        return cls.model_validate(user.model_dump())


class UserListResponse(PagePaginatedResponse[User, UserReadingResponse]):
    @classmethod
    def build_item(cls, user: User) -> UserReadingResponse:
        return UserReadingResponse.from_db_model(user)


class UserSignupInfoResponse(BaseModel):
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()

    @classmethod
    def from_db_model(cls, user: User):
        return cls.model_validate(user.model_dump())


class UserSignupSetPasswordRequest(BaseModel):
    password: str = _UserPasswordField()


class UserAuthenticationRequest(BaseModel):
    email: str = _UserEmailField()
    password: str = _UserPasswordField()


class UserMeResponse(BaseModel):
    id: str = _UserIdField()
    first_name: str = _UserFirstNameField()
    last_name: str = _UserLastNameField()
    email: str = _UserEmailField()
    permissions: ApplicablePermissionsData = _UserPermissionsField()

    @classmethod
    def from_db_model(cls, user: User):
        return cls.model_validate(
            {
                **user.model_dump(exclude={"permissions"}),
                "permissions": compute_applicable_permissions(
                    user.permissions
                ).model_dump(),
            }
        )
