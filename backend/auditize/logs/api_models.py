from datetime import datetime
from typing import Optional, Annotated

from pydantic import ConfigDict, BaseModel, Field, BeforeValidator

from auditize.common.api_models import serialize_datetime, validate_datetime
from auditize.logs.models import Log


class _LogBase(BaseModel):
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

    event: Event
    occurred_at: Annotated[datetime, BeforeValidator(validate_datetime)]
    source: dict[str, str] = Field(default_factory=dict)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Resource] = Field(default=None)
    context: dict[str, dict[str, str]] = Field(default_factory=dict)


class LogCreationRequest(_LogBase):
    def to_log(self) -> Log:
        return Log.model_validate(self.model_dump())


class LogCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)]


class _LogReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)]
    saved_at: datetime


class LogReadingResponse(_LogBase, _LogReadingResponse):
    model_config = ConfigDict(
        json_encoders={datetime: serialize_datetime}
    )

    @classmethod
    def from_log(cls, log: Log):
        return cls.model_validate(log.model_dump())
