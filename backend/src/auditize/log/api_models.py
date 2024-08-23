from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Request
from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    model_serializer,
    model_validator,
)

from auditize.helpers.api.validators import IDENTIFIER_PATTERN
from auditize.helpers.datetime import validate_datetime
from auditize.log.models import Log
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.cursor.api_models import CursorPaginatedResponse
from auditize.resource.pagination.page.api_models import PagePaginatedResponse


class _CustomFieldData(BaseModel):
    name: str = Field(description="Field name", pattern=IDENTIFIER_PATTERN)
    value: str = Field(description="Field value")


def _LogIdField(**kwargs):  # noqa
    return IdField("Log ID", **kwargs)


def _ActionTypeField():  # noqa
    return Field(
        description="Action type",
        json_schema_extra={"example": "create_configuration_profile"},
        pattern=IDENTIFIER_PATTERN,
    )


def _ActionCategoryField():  # noqa
    return Field(
        description="Action category",
        json_schema_extra={"example": "configuration"},
        pattern=IDENTIFIER_PATTERN,
    )


class _ActionData(BaseModel):
    type: str = _ActionTypeField()
    category: str = _ActionCategoryField()


def _ActionField(**kwargs):  # noqa
    return Field(description="Action information", **kwargs)


def _SourceField(**kwargs):  # noqa
    return Field(
        description="Various information about the source of the event such as IP address, User-Agent, etc...",
        json_schema_extra={
            "example": [
                {"name": "ip", "value": "127.0.0.1"},
                {"name": "user_agent", "value": "Mozilla/5.0"},
            ]
        },
        **kwargs,
    )


def _ActorRefField():  # noqa
    return Field(
        description="Actor ref must be unique for a given actor",
        json_schema_extra={"example": "user:123"},
    )


def _ActorTypeField():  # noqa
    return Field(
        description="Actor type",
        json_schema_extra={"example": "user"},
        pattern=IDENTIFIER_PATTERN,
    )


def _ActorNameField():  # noqa
    return Field(description="Actor name", json_schema_extra={"example": "John Doe"})


def _ActorExtraField(**kwargs):  # noqa
    return Field(
        description="Extra actor information",
        json_schema_extra={
            "example": [{"name": "role", "value": "admin"}],
        },
        **kwargs,
    )


class _ActorInputData(BaseModel):
    ref: str = _ActorRefField()
    type: str = _ActorTypeField()
    name: str = _ActorNameField()
    extra: list[_CustomFieldData] = _ActorExtraField(default_factory=list)


class _ActorOutputData(BaseModel):
    ref: str = _ActorRefField()
    type: str = _ActorTypeField()
    name: str = _ActorNameField()
    extra: list[_CustomFieldData] = _ActorExtraField()


def _ActorField(**kwargs):  # noqa
    return Field(description="Actor information", **kwargs)


def _ResourceRefField():  # noqa
    return Field(
        description="Resource ref must be unique for a given resource",
        json_schema_extra={"example": "config-profile:123"},
    )


def _ResourceTypeField():  # noqa
    return Field(
        description="Resource type",
        json_schema_extra={"example": "config-profile"},
        pattern=IDENTIFIER_PATTERN,
    )


def _ResourceNameField():  # noqa
    return Field(
        description="Resource name", json_schema_extra={"example": "Config Profile 123"}
    )


def _ResourceExtraField(**kwargs):  # noqa
    return Field(
        description="Extra resource information",
        json_schema_extra={
            "example": [
                {
                    "name": "description",
                    "value": "Description of the configuration profile",
                }
            ],
        },
        **kwargs,
    )


class _ResourceInputData(BaseModel):
    ref: str = _ResourceRefField()
    type: str = _ResourceTypeField()
    name: str = _ResourceNameField()
    extra: list[_CustomFieldData] = _ResourceExtraField(default_factory=list)


class _ResourceOutputData(BaseModel):
    ref: str = _ResourceRefField()
    type: str = _ResourceTypeField()
    name: str = _ResourceNameField()
    extra: list[_CustomFieldData] = _ResourceExtraField()


def _ResourceField(**kwargs):  # noqa
    return Field(description="Resource information", **kwargs)


def _DetailsField(**kwargs):  # noqa
    return Field(
        description="Details about the action",
        json_schema_extra={
            "example": [
                {"name": "field_name_1", "description": "value_1"},
                {"name": "field_name_2", "description": "value_2"},
            ],
        },
        **kwargs,
    )


def _TagRefField(**kwargs):  # noqa
    return Field(
        description="Tag ref is required for 'rich' tags",
        **kwargs,
    )


def _TagTypeField():  # noqa
    return Field(
        description="If only type is set then it represents a 'simple' tag",
        pattern=IDENTIFIER_PATTERN,
    )


def _TagNameField(**kwargs):  # noqa
    return Field(
        description="Tag name is required for 'rich' tags",
        **kwargs,
    )


class _TagInputData(BaseModel):
    ref: Optional[str] = _TagRefField(default=None)
    type: str = _TagTypeField()
    name: Optional[str] = _TagNameField(default=None)

    model_config = {
        "json_schema_extra": {
            "example": [
                {"type": "security"},
                {
                    "ref": "config-profile:123",
                    "type": "config-profile",
                    "name": "Config Profile 123",
                },
            ]
        }
    }


class _TagOutputData(BaseModel):
    ref: str | None = _TagRefField()
    type: str = _TagTypeField()
    name: str | None = _TagNameField()

    model_config = {
        "json_schema_extra": {
            "example": [
                {"ref": None, "type": "security", "name": None},
                {
                    "ref": "config-profile:123",
                    "type": "config-profile",
                    "name": "Config Profile 123",
                },
            ]
        }
    }


class _EntityData(BaseModel):
    ref: str = Field(description="Entity ref")
    name: str = Field(description="Entity name")


def _EntityPathField():  # noqa
    return Field(
        description="Represents the complete path of the entity that the log is associated with."
        "This array must at least contain one item.",
        json_schema_extra={
            "example": [
                {"ref": "customer:1", "name": "Customer 1"},
                {"ref": "entity:1", "name": "Entity 1"},
            ]
        },
    )


class LogCreationRequest(BaseModel):
    action: _ActionData = _ActionField()
    source: list[_CustomFieldData] = _SourceField(default_factory=list)
    actor: Optional[_ActorInputData] = _ActorField(default=None)
    resource: Optional[_ResourceInputData] = _ResourceField(
        default=None,
    )
    details: list[_CustomFieldData] = _DetailsField(default_factory=list)
    tags: list[_TagInputData] = Field(default_factory=list)
    entity_path: list[_EntityData] = _EntityPathField()

    @model_validator(mode="after")
    def validate_tags(self):
        for tag in self.tags:
            if bool(tag.ref) ^ bool(tag.name):
                raise ValueError("Rich tags require both category and name attributes")
        return self

    @model_validator(mode="after")
    def validate_entity_path(self):
        if len(self.entity_path) == 0:
            raise ValueError("Entity path must be at least one entity deep")
        return self


class LogCreationResponse(BaseModel):
    id: UUID = _LogIdField()


class _AttachmentData(BaseModel, HasDatetimeSerialization):
    name: str
    type: str
    mime_type: str
    saved_at: datetime


class LogReadingResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _LogIdField()
    action: _ActionData = _ActionField()
    source: list[_CustomFieldData] = _SourceField()
    actor: Optional[_ActorOutputData] = _ActorField()
    resource: Optional[_ResourceOutputData] = _ResourceField()
    details: list[_CustomFieldData] = _DetailsField()
    tags: list[_TagOutputData] = Field()
    entity_path: list[_EntityData] = _EntityPathField()
    attachments: list[_AttachmentData] = Field()
    saved_at: datetime


class LogsReadingResponse(CursorPaginatedResponse[Log, LogReadingResponse]):
    @classmethod
    def build_item(cls, log: Log) -> LogReadingResponse:
        return LogReadingResponse.model_validate(log.model_dump())


class NameData(BaseModel):
    name: str


class NameListResponse(PagePaginatedResponse[str, NameData]):
    @classmethod
    def build_item(cls, name: str) -> NameData:
        return NameData(name=name)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [{"name": "identifier_1"}, {"name": "identifier_2"}],
                "pagination": {
                    "page": 1,
                    "page_size": 10,
                    "total": 2,
                    "total_pages": 1,
                },
            }
        }
    )


class EntityItemData(_EntityData):
    parent_entity_ref: str | None = Field(
        description="The ID of the parent entity. It is null for top-level entities.",
    )
    has_children: bool = Field(
        description="Indicates whether the entity has children or not",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ref": "entity:1",
                "name": "Entity 1",
                "parent_entity_ref": "customer:1",
                "has_children": True,
            }
        }
    )


class LogEntityResponse(EntityItemData):
    pass


class LogEntityListResponse(PagePaginatedResponse[Log.Entity, EntityItemData]):
    @classmethod
    def build_item(cls, entity: Log.Entity) -> EntityItemData:
        return EntityItemData.model_validate(entity.model_dump())


class BaseLogSearchParams(BaseModel):
    # All those fields are left Optional[] because FastAPI seems to explicitly pass None
    # (the default value) to the class constructor instead of not passing the value at all.
    # That triggers a pydantic validation error because None is not explicitly allowed.
    # The Optional[] is also needed because (among others) this model is used in GET /users/me/logs/filters
    # for the search_params field (where field values can be None).
    action_type: Optional[str] = Field(default=None)
    action_category: Optional[str] = Field(default=None)
    actor_type: Optional[str] = Field(default=None)
    actor_name: Optional[str] = Field(default=None)
    actor_ref: Optional[str] = Field(default=None)
    resource_type: Optional[str] = Field(default=None)
    resource_name: Optional[str] = Field(default=None)
    resource_ref: Optional[str] = Field(default=None)
    tag_ref: Optional[str] = Field(default=None)
    tag_type: Optional[str] = Field(default=None)
    tag_name: Optional[str] = Field(default=None)
    has_attachment: Optional[bool] = Field(default=None)
    attachment_name: Optional[str] = Field(default=None)
    attachment_type: Optional[str] = Field(default=None)
    attachment_mime_type: Optional[str] = Field(default=None)
    entity_ref: Optional[str] = Field(default=None)
    since: Annotated[Optional[datetime], BeforeValidator(validate_datetime)] = Field(
        default=None
    )
    until: Annotated[Optional[datetime], BeforeValidator(validate_datetime)] = Field(
        default=None
    )


class LogSearchQueryParams(BaseLogSearchParams):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    request: Request

    def _get_custom_field_search_params(self, prefix: str) -> dict[str, str]:
        params = {}
        for param_name, param_value in self.request.query_params.items():
            parts = param_name.split(".")
            if len(parts) == 2 and parts[0] == prefix:
                params[parts[1]] = param_value
        return params

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        serialized = handler(self)
        return {
            **serialized,
            "details": self._get_custom_field_search_params("details"),
            "source": self._get_custom_field_search_params("source"),
            "actor_extra": self._get_custom_field_search_params("actor"),
            "resource_extra": self._get_custom_field_search_params("resource"),
        }
