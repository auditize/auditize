from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field


class CursorPaginationParams(BaseModel):
    cursor: Optional[str] = Field(
        description="The cursor value previously returned in 'next_cursor' "
        "field of the response or no value for the first page.",
        default=None,
    )
    limit: int = Field(
        description="The number of items per page",
        default=10,
        ge=1,
        le=100,
        json_schema_extra={"example": 10},
    )


class CursorPaginationData(BaseModel):
    next_cursor: str | None = Field(
        description="The cursor to the next page of results. It must be passed as the 'cursor' parameter to the "
        "next query to get the next page of results. 'next_cursor' will be null if there "
        "are no more results to fetch."
    )


ModelItemT = TypeVar("ModelItemT")
ApiItemT = TypeVar("ApiItemT")


class CursorPaginatedResponse(BaseModel, Generic[ModelItemT, ApiItemT]):
    pagination: CursorPaginationData = Field(
        description="Cursor-based pagination information"
    )
    items: list[ApiItemT] = Field(description="List of items")

    @classmethod
    def build(cls, items: list[ModelItemT], next_cursor: str = None):
        return cls(
            items=list(map(cls.build_item, items)),
            pagination=CursorPaginationData(next_cursor=next_cursor),
        )

    @classmethod
    def build_item(cls, item: ModelItemT) -> ApiItemT:
        return item
