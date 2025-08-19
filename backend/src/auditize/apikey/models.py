from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import TypeDecorator
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from auditize.database.dbm import Base
from auditize.permissions.models import Permissions, PermissionsInput, PermissionsOutput
from auditize.permissions.operations import normalize_permissions
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse
from auditize.resource.sql_models import HasCreatedAt, HasId


class PermissionsAsJSON(TypeDecorator):
    impl = JSON

    def process_bind_param(self, value: Permissions | Any, _):
        return (
            normalize_permissions(value).model_dump(mode="json")
            if isinstance(value, Permissions)
            else value
        )

    def process_result_value(self, value: dict, _) -> Permissions:
        return Permissions.model_validate(value)


class Apikey(Base, HasId, HasCreatedAt):
    __tablename__ = "apikey"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    key_hash: Mapped[str | None] = mapped_column()
    permissions: Mapped[Permissions] = mapped_column(PermissionsAsJSON())


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


class ApikeyResponse(BaseModel):
    id: UUID = _ApikeyIdField()
    name: str = _ApikeyNameField()
    permissions: PermissionsOutput = _ApikeyPermissionsField()


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
