from datetime import datetime
from typing import Optional
from bson import ObjectId

from pydantic import ConfigDict, BaseModel, Field


class Log(BaseModel):
    class Event(BaseModel):
        name: str
        category: str

    class Actor(BaseModel):
        type: str
        id: str
        name: str

    class Resource(BaseModel):
        type: str
        id: str
        name: str

    id: Optional[ObjectId] = Field(default=None, validation_alias="_id")
    event: Event
    saved_at: datetime = Field(default_factory=datetime.utcnow)
    source: dict[str, str] = Field(default_factory=dict)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Actor] = Field(default=None)
    context: dict[str, dict[str, str]] = Field(default_factory=dict)

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )
