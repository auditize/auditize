from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from auditize.helpers.pagination.page.api_models import PagePaginatedResponse
from auditize.permissions.api_models import ApplicablePermissionsData, PermissionsData
from auditize.permissions.operations import compute_applicable_permissions
from auditize.users.models import User


class UserCreationRequest(BaseModel):
    first_name: str = Field(description="The user first name")
    last_name: str = Field(description="The user last name")
    email: EmailStr = Field(description="The user email")
    permissions: PermissionsData = Field(
        description="The user permissions", default_factory=PermissionsData
    )

    def to_db_model(self):
        return User.model_validate(self.model_dump())


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(description="The user first name", default=None)
    last_name: Optional[str] = Field(description="The user last name", default=None)
    email: Optional[str] = Field(description="The user email", default=None)
    permissions: Optional[PermissionsData] = Field(
        description="The user permissions", default=None
    )


class UserCreationResponse(BaseModel):
    id: str = Field(description="The user id")


class UserReadingResponse(BaseModel):
    id: str = Field(description="The user id")
    first_name: str = Field(description="The user first name")
    last_name: str = Field(description="The user last name")
    email: str = Field(description="The user email")
    permissions: PermissionsData = Field(
        description="The user permissions", default_factory=PermissionsData
    )

    @classmethod
    def from_db_model(cls, user: User):
        return cls.model_validate(user.model_dump())


class UserListResponse(PagePaginatedResponse[User, UserReadingResponse]):
    @classmethod
    def build_item(cls, user: User) -> UserReadingResponse:
        return UserReadingResponse.from_db_model(user)


class UserSignupInfoResponse(BaseModel):
    first_name: str = Field(description="The user first name")
    last_name: str = Field(description="The user last name")
    email: str = Field(description="The user email")

    @classmethod
    def from_db_model(cls, user: User):
        return cls.model_validate(user.model_dump())


class UserSignupSetPasswordRequest(BaseModel):
    password: str = Field(description="The user password")


class UserAuthenticationRequest(BaseModel):
    email: str = Field(description="The user email")
    password: str = Field(description="The user password")


class UserMeResponse(BaseModel):
    id: str = Field(description="The authenticated user id")
    first_name: str = Field(description="The authenticated user first name")
    last_name: str = Field(description="The authenticated user last name")
    email: str = Field(description="The authenticated user email")
    permissions: ApplicablePermissionsData = Field(
        description="The user permissions", default_factory=ApplicablePermissionsData
    )

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
