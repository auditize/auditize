from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

from auditize.apikeys.models import Apikey, ApikeyUpdate
from auditize.common.pagination.page.api_models import PagePaginatedResponse
from auditize.permissions.api_models import PermissionsData


class ApikeyCreationRequest(BaseModel):
    name: str = Field(description="The apikey name")
    permissions: PermissionsData = Field(
        description="The apikey permissions", default_factory=PermissionsData
    )

    def to_db_model(self):
        return Apikey.model_validate(self.model_dump())


class ApikeyUpdateRequest(BaseModel):
    name: Optional[str] = Field(description="The apikey name", default=None)
    permissions: Optional[PermissionsData] = Field(
        description="The apikey permissions", default=None
    )

    def to_db_model(self):
        return ApikeyUpdate.model_validate(self.model_dump(exclude_none=True))


class ApikeyCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The apikey id")
    token: str = Field(description="The apikey token")


class ApikeyReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The apikey id")
    name: str = Field(description="The apikey name")
    permissions: PermissionsData = Field(
        description="The apikey permissions", default_factory=PermissionsData
    )

    @classmethod
    def from_db_model(cls, apikey: Apikey):
        return cls.model_validate(apikey.model_dump())


class ApikeyListResponse(PagePaginatedResponse[Apikey, ApikeyReadingResponse]):
    @classmethod
    def build_item(cls, apikey: Apikey) -> ApikeyReadingResponse:
        return ApikeyReadingResponse.from_db_model(apikey)


class ApikeyTokenGenerationResponse(BaseModel):
    token: str = Field(description="The apikey token")
