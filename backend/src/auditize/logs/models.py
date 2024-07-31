from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field


class CustomField(BaseModel):
    name: str
    value: str


class Log(BaseModel):
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

    class Node(BaseModel):
        ref: str
        name: str

    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )
    action: Action
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: list[CustomField] = Field(default_factory=list)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Resource] = Field(default=None)
    details: list[CustomField] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    attachments: list[AttachmentMetadata] = Field(default_factory=list)
    node_path: list[Node] = Field(default_factory=list)


class Node(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(
        alias="_id",
    )
    ref: str
    name: str
    parent_node_ref: str | None
    has_children: bool
