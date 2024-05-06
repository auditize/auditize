from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

from auditize.common.pagination.page.api_models import PagePaginatedResponse
from auditize.integrations.models import Integration, IntegrationUpdate
from auditize.permissions.api_models import PermissionsData


class IntegrationCreationRequest(BaseModel):
    name: str = Field(description="The integration name")
    permissions: PermissionsData = Field(
        description="The integration permissions", default_factory=PermissionsData
    )

    def to_db_model(self):
        return Integration.model_validate(self.model_dump())


class IntegrationUpdateRequest(BaseModel):
    name: Optional[str] = Field(description="The integration name", default=None)
    permissions: Optional[PermissionsData] = Field(
        description="The integration permissions", default=None
    )

    def to_db_model(self):
        return IntegrationUpdate.model_validate(self.model_dump(exclude_none=True))


class IntegrationCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The integration id")
    token: str = Field(description="The integration token")


class IntegrationReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The integration id")
    name: str = Field(description="The integration name")
    permissions: PermissionsData = Field(
        description="The integration permissions", default_factory=PermissionsData
    )

    @classmethod
    def from_db_model(cls, integration: Integration):
        return cls.model_validate(integration.model_dump())


class IntegrationListResponse(
    PagePaginatedResponse[Integration, IntegrationReadingResponse]
):
    @classmethod
    def build_item(cls, integration: Integration) -> IntegrationReadingResponse:
        return IntegrationReadingResponse.from_db_model(integration)


class IntegrationTokenGenerationResponse(BaseModel):
    token: str = Field(description="The integration token")
