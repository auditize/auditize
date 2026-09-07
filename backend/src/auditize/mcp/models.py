from typing import Generic, TypeVar

from pydantic import BaseModel, Field

ItemT = TypeVar("ItemT")


class PaginatedMcpResponse(BaseModel, Generic[ItemT]):
    items: list[ItemT] = Field(description="Page items")
    next_cursor: str | None = Field(
        default=None,
        description=(
            "If not null, more results are available. Call this same tool again "
            "with `cursor` set to this value to fetch the next page."
        ),
    )


class LogEntityMcpResponse(BaseModel):
    ref: str = Field(description="Entity ref")
    name: str = Field(description="Entity name")
    path: str = Field(
        description="Entity path as a string",
        json_schema_extra={"example": "Customer 1 > Entity 1"},
    )
