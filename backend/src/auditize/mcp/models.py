from datetime import datetime
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


class LogTimeAggregationMcpResponse(BaseModel):
    interval: str = Field(description="Interval of the periods")
    timezone: str = Field(description="Timezone used to compute the periods")
    start: datetime | None = Field(
        description=(
            "Start of the time window: search_params.since if set, otherwise the "
            "date of the oldest matching log (null if there is no matching log)"
        )
    )
    end: datetime | None = Field(
        description=(
            "End of the time window: search_params.until if set, otherwise the "
            "date of the most recent matching log (null if there is no matching log)"
        )
    )
    total_count: int = Field(
        description="Number of logs matching the search params (same as count_logs)"
    )
    timeline: list[dict[str, Any]] = Field(
        description=(
            "One entry per period in chronological order (or hour of day / day of "
            "week order), periods without logs included. Each entry has:\n"
            "- `period`: start of the period as a datetime, an hour of day (0-23) "
            "or a day of week (monday...sunday)\n"
            "- `count`: number of logs in the period\n"
            "- `distinct_count` (only with count_distinct): number of distinct values "
            "of the count_distinct dimension among the logs of the period\n"
            "- `breakdown` (only with split_by): one entry per top value of the "
            "split_by dimension having logs in the period, with one property named "
            "after the dimension, `count` and `distinct_count` (only with "
            "count_distinct)\n"
            "- `other_count` (only with split_by): number of logs of the period that "
            "are not in the breakdown entries"
        ),
        json_schema_extra={
            "example": [
                {
                    "period": "2026-10-16T02:00:00+02:00",
                    "count": 95,
                    "breakdown": [
                        {"actor": {"ref": "user:42", "name": "Alice"}, "count": 60},
                        {"actor": {"ref": "user:7", "name": "Bob"}, "count": 23},
                    ],
                    "other_count": 12,
                }
            ]
        },
    )
