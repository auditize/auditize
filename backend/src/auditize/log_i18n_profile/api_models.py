from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from auditize.i18n.lang import Lang
from auditize.log_i18n_profile.models import LogI18nProfile
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse


class LogTranslation(BaseModel):
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
    return IdField("Profile ID")


def _ProfileCreatedAtField():  # noqa
    return Field()


class LogI18nProfileCreationRequest(BaseModel):
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslation] = _ProfileTranslationsField(
        default_factory=dict
    )


class LogI18nProfileCreationResponse(BaseModel):
    id: UUID = _ProfileIdField()


class LogI18nProfileUpdateRequest(BaseModel):
    name: str = _ProfileNameField(default=None)
    translations: dict[Lang, LogTranslation | None] = _ProfileTranslationsField(
        default=None
    )


class LogI18nProfileReadingResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _ProfileIdField()
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslation] = _ProfileTranslationsField()
    created_at: datetime = _ProfileCreatedAtField()


class LogI18nProfileListResponse(
    PagePaginatedResponse[LogI18nProfile, LogI18nProfileReadingResponse]
):
    @classmethod
    def build_item(cls, profile: LogI18nProfile) -> LogI18nProfileReadingResponse:
        return LogI18nProfileReadingResponse.model_validate(profile.model_dump())
