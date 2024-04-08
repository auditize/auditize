from typing import Generic, TypeVar

from pydantic import BaseModel, Field


class CursorPaginationData(BaseModel):
    next_cursor: str | None = Field(
        description="The cursor to the next page of results. It must be passed as the 'cursor' parameter to the "
                    "next query to get the next page of results. 'next_cursor' will be null if there "
                    "are no more results to fetch."
    )


ModelItemT = TypeVar("ModelItemT")
ApiItemT = TypeVar("ApiItemT")


class CursorPaginatedResponse(BaseModel, Generic[ModelItemT, ApiItemT]):
    pagination: CursorPaginationData = Field(description="Cursor-based pagination information")
    data: list[ApiItemT] = Field(description="List of items")

    @classmethod
    def build(cls, items: list[ModelItemT], next_cursor: str = None):
        return cls(
            data=list(map(cls.build_item, items)),
            pagination=CursorPaginationData(next_cursor=next_cursor)
        )

    @classmethod
    def build_item(cls, item: ModelItemT) -> ApiItemT:
        return item
