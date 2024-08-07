from pydantic import BaseModel, Field

from auditize.resource.models import HasCreatedAt, HasId
from auditize.users.models import Lang


class LogTranslation(BaseModel):
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


class LogI18nProfile(BaseModel, HasId, HasCreatedAt):
    name: str
    translations: dict[Lang, LogTranslation] = Field(default_factory=dict)


class LogI18nProfileUpdate(BaseModel):
    name: str = None
    translations: dict[Lang, LogTranslation | None] = None
