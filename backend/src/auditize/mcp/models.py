from typing import Any, Generic, TypeVar

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


class LogAggregationMcpResponse(BaseModel):
    total_count: int = Field(
        description="Number of logs matching the search params (same as count_logs)"
    )
    rows: list[dict[str, Any]] = Field(
        description=(
            "One row per group (per combination of values with two dimensions), "
            "sorted by count desc. Each row has one property per dimension (named "
            "after the dimension) and a `count` property."
        ),
        json_schema_extra={
            "example": [
                {
                    "actor": {"ref": "user:42", "name": "Alice"},
                    "details.status": "failed",
                    "count": 400,
                }
            ]
        },
    )
    other_count: int = Field(
        description=(
            "Number of logs that are not in the returned rows: logs in groups beyond "
            "the top `limit` groups and logs without value for a dimension"
        )
    )
