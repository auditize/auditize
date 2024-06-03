from typing import Optional

from pydantic import BaseModel, Field

from auditize.apikeys.models import Apikey
from auditize.helpers.pagination.page.api_models import PagePaginatedResponse
from auditize.permissions.api_models import PermissionsInputData, PermissionsOutputData


class ApikeyCreationRequest(BaseModel):
    name: str = Field(description="The API key name")
    permissions: PermissionsInputData = Field(
        description="The API key permissions", default_factory=PermissionsInputData
    )

    def to_db_model(self):
        return Apikey.model_validate(self.model_dump())


class ApikeyUpdateRequest(BaseModel):
    name: Optional[str] = Field(description="The API key name", default=None)
    permissions: Optional[PermissionsInputData] = Field(
        description="The API key permissions", default=None
    )


class ApikeyCreationResponse(BaseModel):
    id: str = Field(description="The API key id")
    key: str = Field(description="The API key secret")


class ApikeyReadingResponse(BaseModel):
    id: str = Field(description="The API key id")
    name: str = Field(description="The API key name")
    permissions: PermissionsOutputData = Field(
        description="The API key permissions",
    )

    @classmethod
    def from_db_model(cls, apikey: Apikey):
        return cls.model_validate(apikey.model_dump())


class ApikeyListResponse(PagePaginatedResponse[Apikey, ApikeyReadingResponse]):
    @classmethod
    def build_item(cls, apikey: Apikey) -> ApikeyReadingResponse:
        return ApikeyReadingResponse.from_db_model(apikey)


class ApikeyRegenerationResponse(BaseModel):
    key: str = Field(description="The new API key secret")
