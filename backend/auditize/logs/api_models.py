from datetime import datetime
from typing import Optional, Annotated

from pydantic import BaseModel, Field, BeforeValidator, field_serializer, model_validator

from auditize.common.api_models import serialize_datetime
from auditize.logs.models import Log


class _LogBase(BaseModel):
    class Event(BaseModel):
        name: str
        category: str

    class Actor(BaseModel):
        type: str
        id: str
        name: str
        extra: dict[str, str] = Field(default_factory=dict)

    class Resource(BaseModel):
        type: str
        id: str
        name: str
        extra: dict[str, str] = Field(default_factory=dict)

    class Tag(BaseModel):
        id: str
        type: Optional[str] = Field(default=None)
        name: Optional[str] = Field(default=None)

    class Node(BaseModel):
        id: str
        name: str

    event: Event
    source: dict[str, str] = Field(default_factory=dict)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Resource] = Field(default=None)
    details: dict[str, dict[str, str]] = Field(default_factory=dict)
    tags: list[Tag] = Field(default_factory=list)
    node_path: list[Node] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tags(self):
        for tag in self.tags:
            if bool(tag.type) ^ bool(tag.name):
                raise ValueError("Rich tags require both type and name attributes")
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
    id: Annotated[str, BeforeValidator(str)]


class _LogReadingResponse(BaseModel):
    class Attachment(BaseModel):
        name: str
        type: str
        mime_type: str

    id: Annotated[str, BeforeValidator(str)]
    saved_at: datetime
    attachments: list[Attachment] = Field(default_factory=list)


class LogReadingResponse(_LogBase, _LogReadingResponse):
    @field_serializer("saved_at", when_used="json")
    def serialize_datetimes(self, value):
        return serialize_datetime(value)

    @classmethod
    def from_log(cls, log: Log):
        return cls.model_validate(log.model_dump())
