from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator

from auditize.integrations.models import Integration, IntegrationUpdate
from auditize.common.pagination.page.api_models import PagePaginatedResponse


class IntegrationCreationRequest(BaseModel):
    name: str = Field(description="The integration name")

    def to_db_model(self):
        return Integration.model_validate(self.model_dump())


class IntegrationUpdateRequest(BaseModel):
    name: str = Field(description="The integration name")

    def to_db_model(self):
        return IntegrationUpdate.model_validate(self.model_dump(exclude_none=True))


class IntegrationCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The integration id")
    token: str = Field(description="The integration token")


class IntegrationReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The integration id")
    name: str = Field(description="The integration name")

    @classmethod
    def from_db_model(cls, integration: Integration):
        return cls.model_validate(integration.model_dump())


class IntegrationListResponse(PagePaginatedResponse[Integration, IntegrationReadingResponse]):
    @classmethod
    def build_item(cls, integration: Integration) -> IntegrationReadingResponse:
        return IntegrationReadingResponse.from_db_model(integration)


class IntegrationTokenGenerationResponse(BaseModel):
    token: str = Field(description="The integration token")
