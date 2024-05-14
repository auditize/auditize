from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    field_serializer,
    model_validator,
)

from auditize.helpers.datetime import serialize_datetime
from auditize.helpers.pagination.cursor.api_models import CursorPaginatedResponse
from auditize.helpers.pagination.page.api_models import PagePaginatedResponse
from auditize.logs.models import Log


class _LogBase(BaseModel):
    class Action(BaseModel):
        type: str = Field(
            title="Action type",
            json_schema_extra={"example": "create_configuration_profile"},
        )
        category: str = Field(
            title="Action category", json_schema_extra={"example": "configuration"}
        )

    class Actor(BaseModel):
        type: str = Field(title="Actor type", json_schema_extra={"example": "user"})
        id: str = Field(
            title="Actor ID",
            description="It must be unique for a given actor type such as"
            "the actor type and the actor ID combined represent a unique actor",
            json_schema_extra={"example": "123"},
        )
        name: str = Field(title="Actor name", json_schema_extra={"example": "John Doe"})
        extra: dict[str, str] = Field(
            default_factory=dict,
            title="Extra actor information",
            json_schema_extra={"example": {"role": "admin"}, "nullable": True},
        )

    class Resource(BaseModel):
        type: str = Field(
            title="Resource type", json_schema_extra={"example": "config-profile"}
        )
        id: str = Field(
            title="Resource ID",
            description="It must be unique for a given resource type such as the resource type and the resource ID"
            "combined represent a unique resource",
            json_schema_extra={"example": "123"},
        )
        name: str = Field(
            title="Resource name", json_schema_extra={"example": "Config Profile 123"}
        )
        extra: dict[str, str] = Field(
            default_factory=dict,
            description="Extra resource information",
            json_schema_extra={
                "example": {"description": "Description of the configuration profile"},
                "nullable": True,
            },
        )

    class Tag(BaseModel):
        id: str = Field(
            title="Tag ID",
            description="Tag ID is the only field required for a 'simple' tag",
        )
        name: Optional[str] = Field(
            title="Tag name",
            description="If name is set then category must also be set to represent a valid 'rich' tag",
            default=None,
            json_schema_extra={"nullable": True},
        )
        category: Optional[str] = Field(
            title="Tag category",
            description="If category is set then name must also be set to represent a valid 'rich' tag",
            default=None,
            json_schema_extra={"nullable": True},
        )

        model_config = {
            "json_schema_extra": {
                "examples": [
                    {"id": "security"},
                    {
                        "id": "config-profile:123",
                        "type": "config-profile",
                        "name": "Config Profile 123",
                    },
                ]
            }
        }

    class Node(BaseModel):
        ref: str = Field(title="Node ref")
        name: str = Field(title="Node name")

    action: Action
    source: dict[str, str] = Field(
        default_factory=dict,
        description="Various information about the source of the event such as IP address, User-Agent, etc...",
        json_schema_extra={"example": {"ip": "1.2.3.4", "user_agent": "Mozilla/5.0"}},
    )
    actor: Optional[Actor] = Field(default=None, json_schema_extra={"nullable": True})
    resource: Optional[Resource] = Field(
        default=None,
        json_schema_extra={
            "nullable": True,
        },
    )
    details: dict[str, dict[str, str]] = Field(
        description="Details of the event, organized as nested objects",
        default_factory=dict,
        json_schema_extra={
            "nullable": True,
            "example": {
                "old_values": {"description": "Former description"},
                "new_values": {"description": "New description"},
            },
        },
    )
    tags: list[Tag] = Field(default_factory=list)
    node_path: list[Node] = Field(
        description="Represents the complete path of the entity that the log is associated with."
        "This array must at least contain one item.",
        json_schema_extra={
            "example": [
                {"ref": "customer:1", "name": "Customer 1"},
                {"ref": "entity:1", "name": "Entity 1"},
            ]
        },
    )

    @model_validator(mode="after")
    def validate_tags(self):
        for tag in self.tags:
            if bool(tag.category) ^ bool(tag.name):
                raise ValueError("Rich tags require both category and name attributes")
        return self

    @model_validator(mode="after")
    def validate_node_path(self):
        if len(self.node_path) == 0:
            raise ValueError("Node path must be at least one node deep")
        return self


class LogCreationRequest(_LogBase):
    def to_log(self) -> Log:
        return Log.model_validate(self.model_dump())


class LogCreationResponse(BaseModel):
    id: str


class _LogReadingResponse(BaseModel):
    class Attachment(BaseModel):
        name: str
        description: Optional[str]
        type: str
        mime_type: str
        saved_at: datetime

        @field_serializer("saved_at", when_used="json")
        def serialize_datetime(self, value):
            return serialize_datetime(value)

    id: str
    saved_at: datetime
    attachments: list[Attachment] = Field(default_factory=list)


class LogReadingResponse(_LogBase, _LogReadingResponse):
    @field_serializer("saved_at", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value)

    @classmethod
    def from_log(cls, log: Log):
        return cls.model_validate(log.model_dump())


class LogsReadingResponse(CursorPaginatedResponse[Log, LogReadingResponse]):
    @classmethod
    def build_item(cls, log: Log) -> LogReadingResponse:
        return LogReadingResponse.from_log(log)


class NameData(BaseModel):
    name: str


class NameListResponse(PagePaginatedResponse[str, NameData]):
    @classmethod
    def build_item(cls, name: str) -> NameData:
        return NameData(name=name)


class LogActionCategoryListResponse(NameListResponse):
    pass


class LogActionTypeListResponse(NameListResponse):
    pass


class LogActorTypeListResponse(PagePaginatedResponse[str, str]):
    pass


class LogResourceTypeListResponse(PagePaginatedResponse[str, str]):
    pass


class LogTagCategoryListResponse(PagePaginatedResponse[str, str]):
    pass


class NodeItem(_LogBase.Node):
    parent_node_ref: str | None = Field(
        description="The ID of the parent node. It is null for top-level nodes."
    )
    has_children: bool = Field(
        description="Indicates whether the node has children or not"
    )


class LogNodeResponse(NodeItem):
    @classmethod
    def from_node(cls, node: Log.Node):
        return cls.model_validate(node.model_dump())


class LogNodeListResponse(PagePaginatedResponse[Log.Node, NodeItem]):
    @classmethod
    def build_item(cls, node: Log.Node) -> NodeItem:
        return NodeItem.model_validate(node.model_dump())
