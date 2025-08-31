from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator

from auditize.i18n.lang import Lang
from auditize.resource.api_models import (
    CreatedAtField,
    HasDatetimeSerialization,
    IdField,
    UpdatedAtField,
)
from auditize.resource.pagination.page.api_models import PagePaginatedResponse

if TYPE_CHECKING:
    from auditize.log_i18n_profile.sql_models import LogI18nProfile


class LogLabels(BaseModel):
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

    def translate(self, category: str, key: str) -> str | None:
        if category == "action_type":
            translations = self.action_type
        elif category == "action_category":
            translations = self.action_category
        elif category == "actor_type":
            translations = self.actor_type
        elif category == "actor":
            translations = self.actor_custom_field
        elif category == "source":
            translations = self.source_field
        elif category == "details":
            translations = self.detail_field
        elif category == "resource_type":
            translations = self.resource_type
        elif category == "resource":
            translations = self.resource_custom_field
        elif category == "tag_type":
            translations = self.tag_type
        elif category == "attachment_type":
            translations = self.attachment_type
        else:
            raise ValueError(f"Unknown label category: {category!r}")
        return translations.get(key, None)


def _build_default_translation(value: str) -> str:
    return " ".join(s.capitalize() for s in value.split("-"))


def get_log_value_translation(
    profile: LogI18nProfile | None, lang: Lang | str, key_type: str, key: str
) -> str:
    translation = None
    if profile:
        translation = profile.get_translation(lang, key_type, key)
    return translation if translation else _build_default_translation(key)


def _ProfileTranslationsField(**kwargs):  # noqa
    return Field(**kwargs)


def _ProfileNameField(**kwargs):  # noqa
    return Field(**kwargs)


def _ProfileIdField():  # noqa
    return IdField("Profile ID")


class LogI18nProfileCreate(BaseModel):
    name: str = _ProfileNameField()
    translations: dict[Lang, LogLabels] = _ProfileTranslationsField(
        default_factory=dict
    )


class LogI18nProfileUpdate(BaseModel):
    name: str = _ProfileNameField(default=None)
    translations: dict[Lang, LogLabels | None] = _ProfileTranslationsField(default=None)


class LogI18nProfileResponse(BaseModel, HasDatetimeSerialization):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = _ProfileIdField()
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()
    name: str = _ProfileNameField()
    translations: dict[Lang, LogLabels] = _ProfileTranslationsField(
        default_factory=dict
    )

    @field_validator("translations", mode="before")
    def validate_translations(
        cls, translations: list[LogLabels]
    ) -> dict[Lang, LogLabels]:
        return {t.lang: t.labels for t in translations}


class LogI18nProfileListResponse(
    PagePaginatedResponse[type["LogI18nProfile"], LogI18nProfileResponse]
):
    @classmethod
    def build_item(cls, profile: LogI18nProfile) -> LogI18nProfileResponse:
        return LogI18nProfileResponse.model_validate(profile)
