from pydantic import BaseModel, Field

from auditize.version import __version__


class InfoResponse(BaseModel):
    auditize_version: str = Field(
        description="The version of Auditize in a `x.y.z` format",
        json_schema_extra={"example": __version__},
    )
