from typing import Optional

from pydantic import BaseModel, Field

from auditize.api.models.cursor_pagination import CursorPaginationParams
from auditize.api.models.page_pagination import PagePaginationParams


class QuerySearchParam(BaseModel):
    q: Optional[str] = Field(description="Search query", default=None)

    # NB: using a field named "query" + `validation_alias="q"` would be a cleaner solution,
    # but FastAPI then shows the field as "query" instead of "q" in the OpenAPI schema.
    # Also see: https://github.com/fastapi/fastapi/issues/12402
    @property
    def query(self) -> Optional[str]:
        return self.q


class PagePaginatedSearchParams(PagePaginationParams, QuerySearchParam):
    pass


class CursorPaginatedSearchParams(CursorPaginationParams, QuerySearchParam):
    pass
