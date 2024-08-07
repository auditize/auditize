from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from auditize.resource.models import HasCreatedAt, HasId


class RepoStatus(str, Enum):
    enabled = "enabled"
    readonly = "readonly"
    disabled = "disabled"


class Repo(BaseModel, HasId, HasCreatedAt):
    name: str
    log_db_name: str = Field(default=None)
    status: RepoStatus = Field(default=RepoStatus.enabled)
    retention_period: int | None = Field(default=None)
    log_i18n_profile_id: Optional[str] = Field(default=None)


class RepoUpdate(BaseModel):
    name: str = None
    status: RepoStatus = None
    retention_period: Optional[int] = None
    log_i18n_profile_id: Optional[str] = None


class RepoStats(BaseModel):
    first_log_date: Optional[datetime] = None
    last_log_date: Optional[datetime] = None
    log_count: int = 0
    storage_size: int = 0
