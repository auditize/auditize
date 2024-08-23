from pydantic import BaseModel, Field

from auditize.i18n.lang import DEFAULT_LANG, Lang
from auditize.resource.models import HasCreatedAt, HasId


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


class LogI18nProfileUpdate(BaseModel):
    name: str = None
    translations: dict[Lang, LogTranslation | None] = None


def _build_default_translation(value: str) -> str:
    return " ".join(s.capitalize() for s in value.split("-"))


def get_log_value_translation(
    profile: LogI18nProfile | None, lang: Lang, key_type: str, key: str
) -> str:
    translation = None
    if profile:
        translation = profile.get_translation(lang, key_type, key)
    return translation if translation else _build_default_translation(key)
