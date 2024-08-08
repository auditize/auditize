from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from auditize.apikey.models import Apikey
from auditize.permissions.api_models import PermissionsInputData, PermissionsOutputData
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse


def _ApikeyNameField(**kwargs):  # noqa
    return Field(
        description="The API key name",
        json_schema_extra={"example": "Integration API key"},
        **kwargs,
    )


def _ApikeyIdField():  # noqa
    return IdField(description="API key ID")


def _ApikeyKeyField(description="The API key secret", **kwargs):  # noqa
    return Field(
        description=description,
        json_schema_extra={
            "example": "aak-_euGzb85ZisAZtwx8d78NtC1ohK5suU7-u_--jIENlU"
        },
        **kwargs,
    )


def _ApikeyPermissionsField(**kwargs):  # noqa
    return Field(
        description="The API key permissions",
        **kwargs,
    )


class ApikeyCreationRequest(BaseModel):
    name: str = _ApikeyNameField()
    permissions: PermissionsInputData = _ApikeyPermissionsField(
        default_factory=PermissionsInputData
    )


class ApikeyUpdateRequest(BaseModel):
    name: str = _ApikeyNameField(default=None)
    permissions: PermissionsInputData = _ApikeyPermissionsField(default=None)


class ApikeyCreationResponse(BaseModel):
    id: UUID = _ApikeyIdField()
    key: str = _ApikeyKeyField()


class ApikeyReadingResponse(BaseModel):
    id: UUID = _ApikeyIdField()
    name: str = _ApikeyNameField()
    permissions: PermissionsOutputData = _ApikeyPermissionsField()


class ApikeyListResponse(PagePaginatedResponse[Apikey, ApikeyReadingResponse]):
    @classmethod
    def build_item(cls, apikey: Apikey) -> ApikeyReadingResponse:
        return ApikeyReadingResponse.model_validate(apikey.model_dump())


class ApikeyRegenerationResponse(BaseModel):
    key: str = _ApikeyKeyField(description="The new API key secret")


class AccessTokenRequest(BaseModel):
    permissions: PermissionsInputData = _ApikeyPermissionsField()


class AccessTokenResponse(BaseModel, HasDatetimeSerialization):
    access_token: str = Field(
        description="The access token",
    )
    expires_at: datetime = Field(
        description="The access token expiration time",
    )
