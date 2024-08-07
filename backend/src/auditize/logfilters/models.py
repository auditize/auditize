from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from auditize.logs.models import BaseLogSearchParams


class LogFilterSearchParams(BaseLogSearchParams):
    # Allow custom fields such as actor.custom_field.
    # The validation of the custom fields is done by the corresponding model
    # in api_models.py.
    model_config = ConfigDict(extra="allow")


class LogFilter(BaseModel):
    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    repo_id: str
    user_id: str
    search_params: LogFilterSearchParams
    columns: list[str]


class LogFilterUpdate(BaseModel):
    name: str = Field(default=None)
    repo_id: str = Field(default=None)
    search_params: LogFilterSearchParams = Field(default=None)
    columns: list[str] = Field(default=None)
