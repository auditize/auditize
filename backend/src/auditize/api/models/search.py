from typing import Optional

from pydantic import BaseModel, Field

from auditize.api.models.page_pagination import PagePaginationParams


class SearchParams(BaseModel):
    query: Optional[str] = Field(
        validation_alias="q", description="Search query", default=None
    )


class PagePaginatedSearchParams(PagePaginationParams, SearchParams):
    pass
