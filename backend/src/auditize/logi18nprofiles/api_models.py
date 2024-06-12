from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from auditize.helpers.datetime import serialize_datetime
from auditize.users.models import Lang


class LogTranslations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # FIXME: check that dict keys are identifiers
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


def _ProfileTranslationsField(**kwargs):  # noqa
    return Field(**kwargs)


def _ProfileNameField(**kwargs):  # noqa
    return Field(**kwargs)


def _ProfileIdField():  # noqa
    return Field()


def _ProfileCreatedAtField():  # noqa
    return Field()


class LogI18nProfileCreationRequest(BaseModel):
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslations] = _ProfileTranslationsField(
        default_factory=dict
    )


class LogI18nProfileCreationResponse(BaseModel):
    id: str = _ProfileIdField()


class LogI18nProfileUpdateRequest(BaseModel):
    name: Optional[str] = _ProfileNameField(default=None)
    translations: Optional[dict[Lang, LogTranslations]] = _ProfileTranslationsField(
        default=None
    )


class LogI18nProfileReadingResponse(BaseModel):
    id: str = _ProfileIdField()
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslations] = _ProfileTranslationsField()
    created_at: datetime = _ProfileCreatedAtField()

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value)
