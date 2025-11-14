from typing import Optional

from pydantic import BaseModel, Field

from auditize.api.models.cursor_pagination import CursorPaginationParams
from auditize.api.models.page_pagination import PagePaginationParams


class QuerySearchParam(BaseModel):
    query: Optional[str] = Field(
        validation_alias="q", description="Search query", default=None
    )


class PagePaginatedSearchParams(PagePaginationParams, QuerySearchParam):
    pass


class CursorPaginatedSearchParams(CursorPaginationParams, QuerySearchParam):
    pass
