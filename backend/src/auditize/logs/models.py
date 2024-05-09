from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


class Log(BaseModel):
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
        category: Optional[str] = Field(default=None)
        name: Optional[str] = Field(default=None)

    class AttachmentMetadata(BaseModel):
        name: str
        description: Optional[str] = Field(default=None)
        type: str
        mime_type: str

    class Attachment(AttachmentMetadata):
        data: bytes

    class Node(BaseModel):
        id: str
        name: str

    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )
    event: Event
    saved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: dict[str, str] = Field(default_factory=dict)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Resource] = Field(default=None)
    details: dict[str, dict[str, str]] = Field(default_factory=dict)
    tags: list[Tag] = Field(default_factory=list)
    attachments: list[AttachmentMetadata] = Field(default_factory=list)
    node_path: list[Node] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)


class Node(BaseModel):
    id: str
    name: str
    parent_node_id: str | None
    has_children: bool
