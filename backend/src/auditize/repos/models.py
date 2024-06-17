from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field


class RepoStatus(str, Enum):
    enabled = "enabled"
    readonly = "readonly"
    disabled = "disabled"


class Repo(BaseModel):
    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )
    name: str
    status: RepoStatus = Field(default=RepoStatus.enabled)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    log_i18n_profile_id: Optional[str] = Field(default=None)


class RepoUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[RepoStatus] = None
    log_i18n_profile_id: Optional[str] = None


class RepoStats(BaseModel):
    first_log_date: Optional[datetime] = None
    last_log_date: Optional[datetime] = None
    log_count: int = 0
    storage_size: int = 0
