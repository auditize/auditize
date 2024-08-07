from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from auditize.resource.pagination.page.models import PagePaginationInfo


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


class PagePaginationData(BaseModel):
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


ModelItemT = TypeVar("ModelItemT")
ApiItemT = TypeVar("ApiItemT")


class PagePaginatedResponse(BaseModel, Generic[ModelItemT, ApiItemT]):
    pagination: PagePaginationData = Field(
        description="Page-based pagination information"
    )
    items: list[ApiItemT] = Field(description="List of items")

    @classmethod
    def build(
        cls, items: list[ModelItemT], pagination: PagePaginationInfo
    ) -> "PagePaginatedResponse[ModelItemT, ApiItemT]":
        return cls(
            items=list(map(cls.build_item, items)),
            pagination=PagePaginationData.model_validate(pagination.model_dump()),
        )

    @classmethod
    def build_item(cls, item: ModelItemT) -> ApiItemT:
        return item
