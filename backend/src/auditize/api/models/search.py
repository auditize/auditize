from typing import Optional

from pydantic import BaseModel, Field


class ResourceSearchParams(BaseModel):
    query: Optional[str] = Field(alias="q", description="Search query", default=None)
