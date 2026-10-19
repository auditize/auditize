from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_serializer

from auditize.api.models.dates import HasDatetimeSerialization
from auditize.helpers.datetime import serialize_datetime
from auditize.log.models import CustomFieldType

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


class DistinctCount(BaseModel):
    count: int = Field(description="Number of distinct items")
    approx: bool = Field(
        description="Whether the count is approximate (above ~3000 distinct items)"
    )


class TypeLogCount(BaseModel):
    name: str = Field(description="Type name")
    logs: int = Field(description="Number of logs")


class ActorTypeStats(TypeLogCount):
    distinct_actors: DistinctCount = Field(
        description="Number of distinct actors (by ref) of this type"
    )


class ResourceTypeStats(TypeLogCount):
    distinct_resources: DistinctCount = Field(
        description="Number of distinct resources (by ref) of this type"
    )


class ActionTypeStats(BaseModel):
    name: str = Field(description="Action type")
    category: str = Field(description="Most frequent category of the action type")
    logs: int = Field(description="Number of logs")


class TruncatedList(BaseModel, Generic[ItemT]):
    total: int = Field(description="Total number of items")
    truncated: bool = Field(
        description="Whether items only contains the most frequent items"
    )
    items: list[ItemT] = Field(description="Items, most frequent first")


class TruncatedDict(BaseModel, Generic[ItemT]):
    total: int = Field(description="Total number of items")
    truncated: bool = Field(description="Whether items only contains part of the items")
    items: dict[str, ItemT] = Field(description="Items by name")


class CustomFieldGroups(BaseModel, Generic[ItemT]):
    source: ItemT = Field(description="Source custom fields")
    details: ItemT = Field(description="Details custom fields")
    actor: ItemT = Field(description="Actor custom fields")
    resource: ItemT = Field(description="Resource custom fields")


class CustomFieldStats(BaseModel):
    type: CustomFieldType = Field(description="Custom field type")
    coverage: float = Field(
        description="Share of logs having the field (between 0 and 1)"
    )
    distinct_values: DistinctCount | None = Field(
        description=(
            "Number of distinct values (null for datetime, string and json fields)"
        )
    )
    values: dict[str, int] | None = Field(
        description=(
            "Number of logs by value, most frequent first (null for datetime, "
            "string and json fields, or when there are too many distinct values)"
        )
    )
    range: list[int | float | datetime] | None = Field(
        description=(
            "[min, max] of the values (only for integer, float and datetime fields)"
        )
    )

    @field_serializer("range", when_used="json")
    def serialize_range(self, value: list | None) -> list | None:
        if value is None:
            return None
        return [
            serialize_datetime(item) if isinstance(item, datetime) else item
            for item in value
        ]


class RepoDescription(BaseModel, HasDatetimeSerialization):
    logs: int = Field(description="Number of logs")
    first_log_at: datetime | None = Field(
        description=(
            "Date of the first log taken into account (within since / until when "
            "given), null if there is no log"
        )
    )
    last_log_at: datetime | None = Field(
        description=(
            "Date of the last log taken into account (within since / until when "
            "given), null if there is no log"
        )
    )
    action_types: TruncatedList[ActionTypeStats] = Field(description="Action types")
    actor_types: list[ActorTypeStats] = Field(
        description="Actor types, most frequent first"
    )
    resource_types: list[ResourceTypeStats] = Field(
        description="Resource types, most frequent first"
    )
    logs_without_actor: int = Field(description="Number of logs without actor")
    logs_without_resource: int = Field(description="Number of logs without resource")
    custom_fields: CustomFieldGroups[TruncatedDict[CustomFieldType]] = Field(
        description="Custom field types by name, most frequent first"
    )


class ActionDescription(BaseModel, HasDatetimeSerialization):
    action_type: str = Field(description="Action type")
    category: str = Field(description="Most frequent category of the action type")
    logs: int = Field(description="Number of logs")
    first_log_at: datetime | None = Field(
        description=(
            "Date of the first log taken into account (within since / until when "
            "given), null if there is no log"
        )
    )
    last_log_at: datetime | None = Field(
        description=(
            "Date of the last log taken into account (within since / until when "
            "given), null if there is no log"
        )
    )
    distinct_actors: DistinctCount = Field(
        description="Number of distinct actors (by ref)"
    )
    actor_types: list[TypeLogCount] = Field(
        description="Actor types, most frequent first"
    )
    resource_types: list[ResourceTypeStats] = Field(
        description="Resource types, most frequent first"
    )
    logs_without_resource: int = Field(description="Number of logs without resource")
    custom_fields: CustomFieldGroups[TruncatedDict[CustomFieldStats]] = Field(
        description=(
            "Custom fields present in the logs, by name, sorted by coverage "
            "then name (a field used with several types is described with its "
            "most recent type)"
        )
    )
