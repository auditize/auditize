from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from auditize.helpers.datetime import serialize_datetime


class ResourceSearchParams(BaseModel):
    query: Optional[str] = Field(alias="q", description="Search query", default=None)


class HasDatetimeSerialization:
    @field_serializer("*", mode="wrap", when_used="json")
    def serialize_datetime(self, value, default_serializer):
        if isinstance(value, datetime):
            return serialize_datetime(value)
        else:
            return default_serializer(value)


def IdField(description, **kwargs):
    return Field(
        description=description,
        json_schema_extra={"example": "FEC4A4E6-AC13-455F-A0F8-E71AA0C37B7D"},
        **kwargs,
    )
