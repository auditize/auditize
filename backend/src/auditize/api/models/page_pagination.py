from typing import Generic, Self, TypeVar

from pydantic import BaseModel, Field


class PagePaginationInfo(BaseModel):
    page: int = Field(
        description="The current page number", json_schema_extra={"example": 1}
    )
    page_size: int = Field(
        description="The number of items per page", json_schema_extra={"example": 10}
    )
    total: int = Field(
        description="The total number of items", json_schema_extra={"example": 50}
    )
    total_pages: int = Field(
        description="The total number of pages", json_schema_extra={"example": 5}
    )

    @classmethod
    def build(cls, page: int, page_size: int, total: int) -> "PagePaginationInfo":
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=(total + page_size - 1) // page_size,
        )


class PagePaginationParams(BaseModel):
    page: int = Field(
        description="The page number to fetch",
        default=1,
        ge=1,
        json_schema_extra={"example": 1},
    )
    page_size: int = Field(
        description="The number of items per page",
        default=10,
        ge=1,
        le=100,
        json_schema_extra={"example": 10},
    )


ModelItemT = TypeVar("ModelItemT")
ApiItemT = TypeVar("ApiItemT")


class PagePaginatedResponse(BaseModel, Generic[ModelItemT, ApiItemT]):
    pagination: PagePaginationInfo = Field(
        description="Page-based pagination information"
    )
    items: list[ApiItemT] = Field(description="List of items")

    @classmethod
    def build(cls, items: list[ModelItemT], pagination: PagePaginationInfo) -> Self:
        return cls(items=list(map(cls.build_item, items)), pagination=pagination)

    @classmethod
    def build_item(cls, item: ModelItemT) -> ApiItemT:
        return item
