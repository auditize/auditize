from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator

from auditize.api.models.common import IdField
from auditize.api.models.dates import (
    CreatedAtField,
    HasDatetimeSerialization,
    UpdatedAtField,
)
from auditize.api.models.page_pagination import PagePaginatedResponse
from auditize.i18n.lang import Lang

if TYPE_CHECKING:
    from auditize.log_i18n_profile.sql_models import LogI18nProfile


class LogLabels(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "required": [
                "action_type",
                "action_category",
                "actor_type",
                "actor_custom_field",
                "actor_custom_field_enum_value",
                "source_field",
                "source_field_enum_value",
                "detail_field",
                "detail_field_enum_value",
                "resource_type",
                "resource_custom_field_enum_value",
                "resource_custom_field",
                "tag_type",
                "attachment_type",
            ]
        },
        extra="forbid",
    )

    # FIXME: check that dict keys are identifiers
    action_type: dict[str, str] = Field(default_factory=dict)
    action_category: dict[str, str] = Field(default_factory=dict)
    actor_type: dict[str, str] = Field(default_factory=dict)
    actor_custom_field: dict[str, str] = Field(default_factory=dict)
    actor_custom_field_enum_value: dict[str, dict[str, str]] = Field(
        default_factory=dict
    )
    source_field: dict[str, str] = Field(default_factory=dict)
    source_field_enum_value: dict[str, dict[str, str]] = Field(default_factory=dict)
    detail_field: dict[str, str] = Field(default_factory=dict)
    detail_field_enum_value: dict[str, dict[str, str]] = Field(default_factory=dict)
    resource_type: dict[str, str] = Field(default_factory=dict)
    resource_custom_field: dict[str, str] = Field(default_factory=dict)
    resource_custom_field_enum_value: dict[str, dict[str, str]] = Field(
        default_factory=dict
    )
    tag_type: dict[str, str] = Field(default_factory=dict)
    attachment_type: dict[str, str] = Field(default_factory=dict)

    def translate(
        self, category: str, key: str, enum_value: str | None = None
    ) -> str | None:
        match category:
            case "action_type":
                translations = self.action_type
            case "action_category":
                translations = self.action_category
            case "actor_type":
                translations = self.actor_type
            case "actor":
                if enum_value:
                    translations = self.actor_custom_field_enum_value[key]
                else:
                    translations = self.actor_custom_field
            case "source":
                if enum_value:
                    translations = self.source_field_enum_value[key]
                else:
                    translations = self.source_field
            case "details":
                if enum_value:
                    translations = self.detail_field_enum_value[key]
                else:
                    translations = self.detail_field
            case "resource_type":
                translations = self.resource_type
            case "resource":
                if enum_value:
                    translations = self.resource_custom_field_enum_value[key]
                else:
                    translations = self.resource_custom_field
            case "tag_type":
                translations = self.tag_type
            case "attachment_type":
                translations = self.attachment_type
            case _:
                raise ValueError(f"Unknown label category: {category!r}")
        return translations.get(enum_value if enum_value else key, None)


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
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "required": ["id", "created_at", "updated_at", "name", "translations"]
        },
    )

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
