from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from auditize.resource.models import HasId


class CustomField(BaseModel):
    name: str
    value: str


class Log(BaseModel, HasId):
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
        ref: Optional[str] = Field(default=None)
        type: str
        name: Optional[str] = Field(default=None)

    class AttachmentMetadata(BaseModel):
        name: str
        type: str
        mime_type: str
        saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Attachment(AttachmentMetadata):
        data: bytes

    class Entity(BaseModel):
        ref: str
        name: str

    action: Action
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: list[CustomField] = Field(default_factory=list)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Resource] = Field(default=None)
    details: list[CustomField] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    attachments: list[AttachmentMetadata] = Field(default_factory=list)
    entity_path: list[Entity] = Field(default_factory=list)


class Entity(BaseModel, HasId):
    ref: str
    name: str
    parent_entity_ref: str | None
    has_children: bool


class BaseLogSearchParams(BaseModel):
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
    since: Optional[datetime] = Field(default=None)
    until: Optional[datetime] = Field(default=None)


class LogSearchParams(BaseLogSearchParams):
    actor_extra: Optional[dict] = Field(default=None)
    resource_extra: Optional[dict] = Field(default=None)
    source: Optional[dict] = Field(default=None)
    details: Optional[dict] = Field(default=None)
