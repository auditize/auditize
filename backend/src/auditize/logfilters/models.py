from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field


class LogFilterSearchParams(BaseModel):
    # Allow custom fields such as actor.custom_field.
    # The validation of the custom fields is done by the corresponding model
    # in api_models.py.
    model_config = ConfigDict(extra="allow")

    action_type: Optional[str] = Field(default=None)
    action_category: Optional[str] = Field(default=None)
    actor_type: Optional[str] = Field(default=None)
    actor_name: Optional[str] = Field(default=None)
    actor_ref: Optional[str] = Field(default=None)
    resource_type: Optional[str] = Field(default=None)
    resource_name: Optional[str] = Field(default=None)
    resource_ref: Optional[str] = Field(default=None)
    tag_ref: Optional[str] = Field(default=None)
    tag_type: Optional[str] = Field(default=None)
    tag_name: Optional[str] = Field(default=None)
    has_attachment: Optional[bool] = Field(default=None)
    attachment_name: Optional[str] = Field(default=None)
    attachment_type: Optional[str] = Field(default=None)
    attachment_mime_type: Optional[str] = Field(default=None)
    node_ref: Optional[str] = Field(default=None)
    since: Optional[datetime] = Field(default=None)
    until: Optional[datetime] = Field(default=None)


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
