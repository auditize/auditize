from pydantic import Field


def IdField(description, **kwargs):
    return Field(
        description=description,
        json_schema_extra={"example": "FEC4A4E6-AC13-455F-A0F8-E71AA0C37B7D"},
        **kwargs,
    )
