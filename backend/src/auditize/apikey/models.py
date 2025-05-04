from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from auditize.permissions.models import Permissions, PermissionsInput, PermissionsOutput
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.models import HasCreatedAt, HasId
from auditize.resource.pagination.page.api_models import PagePaginatedResponse


class Apikey(BaseModel, HasId, HasCreatedAt):
    name: str
    key_hash: Optional[str] = None
    permissions: Permissions = Field(default_factory=Permissions)


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


class ApikeyRead(BaseModel):
    id: UUID = _ApikeyIdField()
    name: str = _ApikeyNameField()
    permissions: PermissionsOutput = _ApikeyPermissionsField()


class ApikeyCreateResponse(ApikeyRead):
    key: str = _ApikeyKeyField()


class ApikeyList(PagePaginatedResponse[Apikey, ApikeyRead]):
    @classmethod
    def build_item(cls, apikey: Apikey) -> ApikeyRead:
        return ApikeyRead.model_validate(apikey.model_dump())


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
