from pydantic import BaseModel, ConfigDict, Field

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


def _ProfileTranslationsField():  # noqa
    return Field(default_factory=dict)


def _ProfileNameField():  # noqa
    return Field()


def _ProfileIdField():  # noqa
    return Field()


class LogI18nProfileCreationRequest(BaseModel):
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslations] = _ProfileTranslationsField()


class LogI18nProfileCreationResponse(BaseModel):
    id: str = _ProfileIdField()
