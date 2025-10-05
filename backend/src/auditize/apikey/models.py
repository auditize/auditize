from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from auditize.api.models.common import IdField
from auditize.api.models.dates import (
    CreatedAtField,
    HasDatetimeSerialization,
    UpdatedAtField,
)
from auditize.api.models.page_pagination import PagePaginatedResponse
from auditize.apikey.sql_models import Apikey
from auditize.permissions.models import Permissions, PermissionsInput, PermissionsOutput
from auditize.permissions.service import build_permissions_output


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


class ApikeyCreate(BaseModel):
    name: str = _ApikeyNameField()
    permissions: PermissionsInput = _ApikeyPermissionsField(
        default_factory=PermissionsInput
    )


class ApikeyUpdate(BaseModel):
    name: str = _ApikeyNameField(default=None)
    permissions: PermissionsInput = _ApikeyPermissionsField(default=None)


class ApikeyResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _ApikeyIdField()
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()
    name: str = _ApikeyNameField()
    permissions: PermissionsOutput = _ApikeyPermissionsField()

    @field_validator("permissions", mode="before")
    def validate_permissions(cls, permissions: Permissions):
        return build_permissions_output(permissions)


class ApikeyCreateResponse(ApikeyResponse):
    key: str = _ApikeyKeyField()


class ApikeyListResponse(PagePaginatedResponse[Apikey, ApikeyResponse]):
    @classmethod
    def build_item(cls, apikey: Apikey) -> ApikeyResponse:
        return ApikeyResponse.model_validate(apikey, from_attributes=True)


class ApikeyRegenerationResponse(BaseModel):
    key: str = _ApikeyKeyField(description="The new API key secret")


class AccessTokenRequest(BaseModel):
    permissions: PermissionsInput = _ApikeyPermissionsField()


class AccessTokenResponse(BaseModel, HasDatetimeSerialization):
    access_token: str = Field(
        description="The access token",
    )
    expires_at: datetime = Field(
        description="The access token expiration time",
    )
