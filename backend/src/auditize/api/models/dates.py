from datetime import datetime

from pydantic import Field, field_serializer

from auditize.helpers.datetime import serialize_datetime


class HasDatetimeSerialization:
    @field_serializer("*", mode="wrap", when_used="json")
    def serialize_datetime(self, value, default_serializer):
        if isinstance(value, datetime):
            return serialize_datetime(value)
        else:
            return default_serializer(value)


def CreatedAtField(**kwargs):
    return Field(
        description="The creation date",
        json_schema_extra={"example": "2021-10-12T09:00:00.000Z"},
        **kwargs,
    )


def UpdatedAtField(**kwargs):
    return Field(
        description="The last update date",
        json_schema_extra={"example": "2021-10-12T09:00:00.000Z"},
        **kwargs,
    )
