import enum
import json
from datetime import datetime, timezone
from typing import Annotated, Any, ClassVar, Optional, Self
from uuid import UUID

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    ValidationInfo,
    model_serializer,
    model_validator,
)

from auditize.api.models.common import IdField
from auditize.api.models.cursor_pagination import (
    CursorPaginatedResponse,
    CursorPaginationParams,
)
from auditize.api.models.dates import HasDatetimeSerialization
from auditize.api.models.search import QuerySearchParam
from auditize.api.validation import IDENTIFIER_PATTERN
from auditize.helpers.datetime import serialize_datetime
from auditize.helpers.string import validate_empty_string_as_none


class CustomFieldType(enum.StrEnum):
    STRING = "string"
    ENUM = "enum"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    INTEGER = "integer"
    FLOAT = "float"
    JSON = "json"


class CustomField(BaseModel):
    """
    Pydantic model for a custom field (name / value pair).
    """

    type: CustomFieldType = Field(default=CustomFieldType.STRING)
    name: str
    value: str | bool | int | float

    _ES_MAPPING: ClassVar[dict[CustomFieldType, str]] = {
        CustomFieldType.ENUM: "value_enum",
        CustomFieldType.BOOLEAN: "value_boolean",
        CustomFieldType.INTEGER: "value_integer",
        CustomFieldType.FLOAT: "value_float",
        CustomFieldType.DATETIME: "value_datetime",
    }

    @model_serializer(mode="wrap")
    def serialize_model(
        self, handler: SerializerFunctionWrapHandler, info: ValidationInfo
    ) -> dict:
        serialized = handler(self)
        if info.context != "es":
            return serialized

        es_field_name = self._ES_MAPPING.get(self.type, "value")
        serialized[es_field_name] = serialized.pop("value")

        return serialized

    @model_validator(mode="before")
    @classmethod
    def pre_validation(cls, data: Any, info: ValidationInfo) -> Any:
        if info.context != "es":
            return data

        pre_validated = data.copy()

        es_field_type = pre_validated.get("type", CustomFieldType.STRING)
        es_field_name = cls._ES_MAPPING.get(es_field_type, "value")
        pre_validated["value"] = pre_validated.pop(es_field_name)

        return pre_validated


class Log(BaseModel):
    """
    Pydantic model for a log that is intended to be stored in Elasticsearch.
    """

    class Action(BaseModel):
        type: str
        category: str

    class Actor(BaseModel):
        ref: str
        type: str
        name: str
        extra: list[CustomField] = Field(default_factory=list)

    class Resource(BaseModel):
        ref: str
        type: str
        name: str
        extra: list[CustomField] = Field(default_factory=list)

    class Tag(BaseModel):
        ref: Optional[str] = None
        type: str
        name: Optional[str] = None

    class AttachmentMetadata(BaseModel):
        name: str
        type: str
        mime_type: str
        saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Attachment(AttachmentMetadata):
        data: bytes

    class EntityPathNode(BaseModel):
        ref: str
        name: str

    id: Optional[UUID] = Field(default=None)
    action: Action
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: list[CustomField] = Field(default_factory=list)
    actor: Optional[Actor] = None
    resource: Optional[Resource] = None
    details: list[CustomField] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    attachments: list[AttachmentMetadata] = Field(default_factory=list)
    entity_path: list[EntityPathNode] = Field(default_factory=list)

    @model_serializer(mode="wrap")
    def serialize_model(
        self, handler: SerializerFunctionWrapHandler, info: ValidationInfo
    ) -> dict:
        serialized = handler(self)
        if info.context != "es":
            return serialized
        serialized["log_id"] = serialized.pop("id")
        return serialized

    @model_validator(mode="before")
    @classmethod
    def pre_validation(cls, data: Any, info: ValidationInfo) -> Any:
        if info.context != "es":
            return data
        pre_validated = data.copy()
        pre_validated["id"] = pre_validated.pop("log_id")
        return pre_validated


def _CustomFieldTypeField(**kwargs):  # noqa
    return Field(description="Field type", **kwargs)


def _CustomFieldNameField(**kwargs):  # noqa
    return Field(description="Field name", pattern=IDENTIFIER_PATTERN, **kwargs)


def _CustomFieldValueField(**kwargs):  # noqa
    return Field(description="Field value", **kwargs)


class _CustomFieldInputData(BaseModel):
    type: CustomFieldType = _CustomFieldTypeField(default=None)
    name: str = _CustomFieldNameField()
    value: str | bool | int | float = _CustomFieldValueField()

    @model_validator(mode="after")
    def post_validate(self) -> Self:
        if self.type:
            # If the type is set, validate the value against the type
            # (both Python type and value format)
            match self.type:
                case CustomFieldType.STRING | CustomFieldType.ENUM:
                    if not isinstance(self.value, str):
                        raise ValueError("Value must be a string")
                case CustomFieldType.DATETIME:
                    if not isinstance(self.value, str):
                        raise ValueError("Value must be a string in ISO 8601 format")
                    try:
                        self.value = serialize_datetime(self.value)
                    except ValueError:
                        raise ValueError(
                            "Value must be a valid datetime in ISO 8601 format"
                        )
                case CustomFieldType.BOOLEAN:
                    if not isinstance(self.value, bool):
                        raise ValueError("Value must be a boolean")
                case CustomFieldType.INTEGER:
                    if not isinstance(self.value, int):
                        raise ValueError("Value must be an integer")
                case CustomFieldType.FLOAT:
                    if not isinstance(self.value, float):
                        raise ValueError("Value must be a float")
                case CustomFieldType.JSON:
                    if not isinstance(self.value, str):
                        raise ValueError("Value must be a valid JSON string")
                    try:
                        json.loads(self.value)
                    except json.JSONDecodeError:
                        raise ValueError("Value must be a valid JSON string")
        else:
            # If the type is NOT set, infer it from the value
            match self.value:
                case bool():
                    self.type = CustomFieldType.BOOLEAN
                case int():
                    self.type = CustomFieldType.INTEGER
                case float():
                    self.type = CustomFieldType.FLOAT
                case _:
                    self.type = CustomFieldType.STRING

        return self


class _CustomFieldOutputData(BaseModel):
    type: CustomFieldType = _CustomFieldTypeField()
    name: str = _CustomFieldNameField()
    value: str | bool | int | float = _CustomFieldValueField()


def _LogIdField(**kwargs):  # noqa
    return IdField("Log ID", **kwargs)


def _ActionTypeField():  # noqa
    return Field(
        description="Action type",
        json_schema_extra={"example": "create-configuration-profile"},
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
                {"name": "user-agent", "value": "Mozilla/5.0"},
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
    extra: list[_CustomFieldInputData] = _ActorExtraField(default_factory=list)


class _ActorOutputData(BaseModel):
    ref: str = _ActorRefField()
    type: str = _ActorTypeField()
    name: str = _ActorNameField()
    extra: list[_CustomFieldOutputData] = _ActorExtraField()


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
    extra: list[_CustomFieldInputData] = _ResourceExtraField(default_factory=list)


class _ResourceOutputData(BaseModel):
    ref: str = _ResourceRefField()
    type: str = _ResourceTypeField()
    name: str = _ResourceNameField()
    extra: list[_CustomFieldOutputData] = _ResourceExtraField()


def _ResourceField(**kwargs):  # noqa
    return Field(description="Resource information", **kwargs)


def _DetailsField(**kwargs):  # noqa
    return Field(
        description="Details about the action",
        json_schema_extra={
            "example": [
                {"name": "field-name-1", "value": "value 1"},
                {"name": "field-name-2", "value": "value 2"},
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
            "examples": [
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
            "examples": [
                {"ref": None, "type": "security", "name": None},
                {
                    "ref": "config-profile:123",
                    "type": "config-profile",
                    "name": "Config Profile 123",
                },
            ]
        }
    }


class _EntityPathNodeData(BaseModel):
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


class LogCreate(BaseModel):
    action: _ActionData = _ActionField()
    source: list[_CustomFieldInputData] = _SourceField(default_factory=list)
    actor: Optional[_ActorInputData] = _ActorField(default=None)
    resource: Optional[_ResourceInputData] = _ResourceField(
        default=None,
    )
    details: list[_CustomFieldInputData] = _DetailsField(default_factory=list)
    tags: list[_TagInputData] = Field(default_factory=list)
    entity_path: list[_EntityPathNodeData] = _EntityPathField()

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


class _LogImport(BaseModel):
    id: UUID = Field(default=None)
    saved_at: datetime = Field(default=None)


class LogImport(LogCreate, _LogImport):
    # NB: we create two model classes _LogImport and LogImport to force the id and saved_at
    # fields to be at the top of the model in OpenAPI schema.
    pass


class LogCreationResponse(BaseModel):
    id: UUID = _LogIdField()


class _AttachmentData(BaseModel, HasDatetimeSerialization):
    name: str
    type: str
    mime_type: str
    saved_at: datetime


class LogResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _LogIdField()
    action: _ActionData = _ActionField()
    source: list[_CustomFieldOutputData] = _SourceField()
    actor: _ActorOutputData | None = _ActorField()
    resource: _ResourceOutputData | None = _ResourceField()
    details: list[_CustomFieldOutputData] = _DetailsField()
    tags: list[_TagOutputData] = Field()
    entity_path: list[_EntityPathNodeData] = _EntityPathField()
    attachments: list[_AttachmentData] = Field()
    saved_at: datetime


class LogListResponse(CursorPaginatedResponse[Log, LogResponse]):
    @classmethod
    def build_item(cls, log: Log) -> LogResponse:
        return LogResponse.model_validate(log.model_dump())


class LogActionTypeListParams(CursorPaginationParams):
    category: Optional[str] = Field(
        default=None, description="The action category to filter by"
    )


class NameData(BaseModel):
    name: str


class NameListResponse(CursorPaginatedResponse[str, NameData]):
    @classmethod
    def build_item(cls, name: str) -> NameData:
        return NameData(name=name)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [{"name": "identifier-1"}, {"name": "identifier-2"}],
                "pagination": {"next_cursor": None},
            }
        }
    )


class NameRefPairData(BaseModel):
    name: str
    ref: str


class NameRefPairListResponse(
    CursorPaginatedResponse[tuple[str, str], NameRefPairData]
):
    @classmethod
    def build_item(cls, name_ref_pair: tuple[str, str]) -> NameRefPairData:
        name, ref = name_ref_pair
        return NameRefPairData(name=name, ref=ref)


class CustomFieldData(BaseModel):
    name: str = Field(description="Custom field name")
    type: CustomFieldType = Field(description="Custom field type")


class CustomFieldListResponse(
    CursorPaginatedResponse[tuple[str, CustomFieldType], CustomFieldData]
):
    @classmethod
    def build_item(cls, custom_field: tuple[str, CustomFieldType]) -> CustomFieldData:
        name, type = custom_field
        return CustomFieldData(name=name, type=type)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {"name": "profile-name", "type": "string"},
                    {"name": "status", "type": "enum"},
                ],
                "pagination": {"next_cursor": None},
            }
        }
    )


class CustomFieldEnumValueData(BaseModel):
    value: str


class CustomFieldEnumValueListResponse(
    CursorPaginatedResponse[str, CustomFieldEnumValueData]
):
    @classmethod
    def build_item(cls, value: str) -> CustomFieldEnumValueData:
        return CustomFieldEnumValueData(value=value)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [{"value": "enabled"}, {"value": "disabled"}],
                "pagination": {"next_cursor": None},
            }
        }
    )


class LogEntityResponse(_EntityPathNodeData):
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


class LogActorResponse(_ActorOutputData):
    pass


class LogResourceResponse(_ResourceOutputData):
    pass


class LogTagResponse(_TagOutputData):
    pass


class LogEntityListParams(CursorPaginationParams):
    root: bool = Field(
        default=False, description="Whether to list top-level entities or not"
    )
    parent_entity_ref: Optional[str] = Field(
        default=None, description="The ref of the parent entity to filter by"
    )


class LogEntityListResponse(
    CursorPaginatedResponse[Log.EntityPathNode, LogEntityResponse]
):
    @classmethod
    def build_item(cls, entity: Log.EntityPathNode) -> LogEntityResponse:
        return LogEntityResponse.model_validate(entity, from_attributes=True)


class BaseLogSearchParams(QuerySearchParam):
    # All those fields are left Optional[] because FastAPI seems to explicitly pass None
    # (the default value) to the class constructor instead of not passing the value at all.
    # That triggers a pydantic validation error because None is not explicitly allowed.
    # The Optional[] is also needed because (among others) this model is used in GET /users/me/logs/filters
    # for the search_params field (where field values can be None).
    action_type: Optional[str] = Field(
        description="Filter logs by action type",
        json_schema_extra={"example": "create-configuration-profile"},
        default=None,
    )
    action_category: Optional[str] = Field(
        description="Filter logs by action category",
        json_schema_extra={"example": "configuration"},
        default=None,
    )
    actor_type: Optional[str] = Field(
        description="Filter logs by actor type",
        json_schema_extra={"example": "user"},
        default=None,
    )
    actor_name: Optional[str] = Field(
        description="Filter logs by actor name",
        json_schema_extra={"example": "John Doe"},
        default=None,
    )
    actor_ref: Optional[str] = Field(
        description="Filter logs by actor reference",
        json_schema_extra={"example": "user:123"},
        default=None,
    )
    resource_type: Optional[str] = Field(
        description="Filter logs by resource type",
        json_schema_extra={"example": "config-profile"},
        default=None,
    )
    resource_name: Optional[str] = Field(
        description="Filter logs by resource name",
        json_schema_extra={"example": "Config Profile 123"},
        default=None,
    )
    resource_ref: Optional[str] = Field(
        description="Filter logs by resource reference",
        json_schema_extra={"example": "config-profile:123"},
        default=None,
    )
    tag_ref: Optional[str] = Field(
        description="Filter logs by tag reference",
        json_schema_extra={"example": "config-profile:123"},
        default=None,
    )
    tag_type: Optional[str] = Field(
        description="Filter logs by tag type",
        json_schema_extra={"example": "security"},
        default=None,
    )
    tag_name: Optional[str] = Field(
        description="Filter logs by tag name",
        json_schema_extra={"example": "Config Profile 123"},
        default=None,
    )
    has_attachment: Optional[bool] = Field(
        description="Filter logs by presence of attachments",
        json_schema_extra={"example": True},
        default=None,
    )
    attachment_name: Optional[str] = Field(
        description="Filter logs by attachment name",
        json_schema_extra={"example": "document.pdf"},
        default=None,
    )
    attachment_type: Optional[str] = Field(
        description="Filter logs by attachment type",
        json_schema_extra={"example": "document"},
        default=None,
    )
    attachment_mime_type: Optional[str] = Field(
        description="Filter logs by attachment MIME type",
        json_schema_extra={"example": "application/pdf"},
        default=None,
    )
    entity_ref: Optional[str] = Field(
        description="Filter logs by entity reference",
        json_schema_extra={"example": "entity:123"},
        default=None,
    )
    since: Annotated[
        Optional[datetime], BeforeValidator(validate_empty_string_as_none)
    ] = Field(
        description="Filter logs created after this datetime",
        json_schema_extra={"example": "2024-01-01T00:00:00.000Z"},
        default=None,
    )
    until: Annotated[
        Optional[datetime], BeforeValidator(validate_empty_string_as_none)
    ] = Field(
        description="Filter logs created before this datetime",
        json_schema_extra={"example": "2024-12-31T23:59:59.999Z"},
        default=None,
    )


class LogSearchParams(BaseLogSearchParams):
    actor_extra: Optional[dict] = None
    resource_extra: Optional[dict] = None
    source: Optional[dict] = None
    details: Optional[dict] = None


class LogSearchQueryParams(BaseLogSearchParams):
    model_config = ConfigDict(extra="allow")

    def _get_custom_field_search_params(self, prefix: str) -> dict[str, str]:
        params = {}
        if self.__pydantic_extra__:
            for param_name, param_value in self.__pydantic_extra__.items():
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


class LogListParams(CursorPaginationParams, LogSearchQueryParams):
    pass


LOG_CSV_BUILTIN_COLUMNS = (
    "log_id",
    "saved_at",
    "action_type",
    "action_category",
    "actor_ref",
    "actor_type",
    "actor_name",
    "resource_ref",
    "resource_type",
    "resource_name",
    "tag_ref",
    "tag_type",
    "tag_name",
    "attachment_name",
    "attachment_type",
    "attachment_mime_type",
    "entity_path:ref",
    "entity_path:name",
)

_COLUMNS_DESCRIPTION = f"""
Comma-separated list of columns to include in the CSV output. Available columns are:
{"\n".join(f"- `{col}`" for col in LOG_CSV_BUILTIN_COLUMNS)}
- `source.<custom-field>`
- `actor.<custom-field>`
- `resource.<custom-field>`
- `details.<custom-field>`

Example of column name if you have a "role" custom field for the actor: `actor.role`.

"""


class LogsAsCsvParams(LogSearchQueryParams):
    columns: str = Field(
        description=_COLUMNS_DESCRIPTION, default=",".join(LOG_CSV_BUILTIN_COLUMNS)
    )
