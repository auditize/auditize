from datetime import datetime, timezone
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

from auditize.users.models import Lang


class LogTranslations(BaseModel):
    action_type: dict[str, str] = Field(default_factory=dict)
    action_category: dict[str, str] = Field(default_factory=dict)
    actor_type: dict[str, str] = Field(default_factory=dict)
    actor_custom_field: dict[str, str] = Field(default_factory=dict)
    source_field: dict[str, str] = Field(default_factory=dict)
    detail_field: dict[str, str] = Field(default_factory=dict)
    resource_type: dict[str, str] = Field(default_factory=dict)
    resource_custom_field: dict[str, str] = Field(default_factory=dict)
    tag_type: dict[str, str] = Field(default_factory=dict)
    attachment_type: dict[str, str] = Field(default_factory=dict)


class LogI18nProfile(BaseModel):
    id: Annotated[Optional[str], BeforeValidator(str)] = Field(
        default=None,
        alias="_id",
    )
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    translations: dict[Lang, LogTranslations] = Field(default_factory=dict)


class LogI18nProfileUpdate(BaseModel):
    name: Optional[str] = None
    translations: Optional[dict[Lang, LogTranslations | None]] = None
