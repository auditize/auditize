from typing import Annotated, Optional

from pydantic import BaseModel, Field, BeforeValidator

from auditize.users.models import User, UserUpdate
from auditize.common.pagination.page.api_models import PagePaginatedResponse


class UserCreationRequest(BaseModel):
    first_name: str = Field(description="The user first name")
    last_name: str = Field(description="The user last name")
    email: str = Field(description="The user email")

    def to_db_model(self):
        return User.model_validate(self.model_dump())


class UserUpdateRequest(BaseModel):
    first_name: Optional[str] = Field(description="The user first name", default=None)
    last_name: Optional[str] = Field(description="The user last name", default=None)
    email: Optional[str] = Field(description="The user email", default=None)

    def to_db_model(self):
        return UserUpdate.model_validate(self.model_dump(exclude_none=True))


class UserCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The user id")


class UserReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The user id")
    first_name: str = Field(description="The user first name")
    last_name: str = Field(description="The user last name")
    email: str = Field(description="The user email")

    @classmethod
    def from_db_model(cls, user: User):
        return cls.model_validate(user.model_dump())


class UserListResponse(PagePaginatedResponse[User, UserReadingResponse]):
    @classmethod
    def build_item(cls, user: User) -> UserReadingResponse:
        return UserReadingResponse.from_db_model(user)
