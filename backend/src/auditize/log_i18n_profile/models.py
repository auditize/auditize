from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from auditize.i18n.lang import DEFAULT_LANG, Lang
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.models import HasCreatedAt, HasId
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

    def get_translation(self, key_type: str, key: str) -> str | None:
        if key_type == "action_type":
            translations = self.action_type
        elif key_type == "action_category":
            translations = self.action_category
        elif key_type == "actor_type":
            translations = self.actor_type
        elif key_type == "actor":
            translations = self.actor_custom_field
        elif key_type == "source":
            translations = self.source_field
        elif key_type == "details":
            translations = self.detail_field
        elif key_type == "resource_type":
            translations = self.resource_type
        elif key_type == "resource":
            translations = self.resource_custom_field
        elif key_type == "tag_type":
            translations = self.tag_type
        elif key_type == "attachment_type":
            translations = self.attachment_type
        else:
            raise ValueError(f"Unknown key_type: {key_type!r}")
        return translations.get(key, None)


class LogI18nProfile(BaseModel, HasId, HasCreatedAt):
    name: str
    translations: dict[Lang, LogTranslation] = Field(default_factory=dict)

    def get_translation(self, lang: Lang, key_type: str, key: str) -> str | None:
        actual_lang = None
        if lang in self.translations:
            actual_lang = lang
        elif DEFAULT_LANG in self.translations:
            actual_lang = DEFAULT_LANG
        if actual_lang:
            return self.translations[actual_lang].get_translation(key_type, key)
        return None


def _build_default_translation(value: str) -> str:
    return " ".join(s.capitalize() for s in value.split("-"))


def get_log_value_translation(
    profile: LogI18nProfile | None, lang: Lang, key_type: str, key: str
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


def _ProfileCreatedAtField():  # noqa
    return Field()


class LogI18nProfileCreate(BaseModel):
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslation] = _ProfileTranslationsField(
        default_factory=dict
    )


class LogI18nProfileUpdate(BaseModel):
    name: str = _ProfileNameField(default=None)
    translations: dict[Lang, LogTranslation | None] = _ProfileTranslationsField(
        default=None
    )


class LogI18nProfileRead(BaseModel, HasDatetimeSerialization):
    id: UUID = _ProfileIdField()
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslation] = _ProfileTranslationsField()
    created_at: datetime = _ProfileCreatedAtField()


class LogI18nProfileList(PagePaginatedResponse[LogI18nProfile, LogI18nProfileRead]):
    @classmethod
    def build_item(cls, profile: LogI18nProfile) -> LogI18nProfileRead:
        return LogI18nProfileRead.model_validate(profile.model_dump())
