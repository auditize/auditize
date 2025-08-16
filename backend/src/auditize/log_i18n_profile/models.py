import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import JSON, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.dbm import Base
from auditize.i18n.lang import DEFAULT_LANG, Lang
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse
from auditize.resource.sql_models import HasCreatedAt, HasId


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


class LogTranslationForLang(Base):
    __tablename__ = "log_i18n_profile_translation"

    id: Mapped[int] = mapped_column(primary_key=True)
    lang: Mapped[Lang] = mapped_column(nullable=False)
    profile_id: Mapped[Uuid] = mapped_column(
        ForeignKey("log_i18n_profile.id", ondelete="CASCADE"), nullable=False
    )
    data: Mapped[JSON] = mapped_column(JSON(), nullable=False)

    @property
    def translation(self) -> LogTranslation:
        return LogTranslation.model_validate(self.data)


class LogI18nProfile(Base, HasId, HasCreatedAt):
    __tablename__ = "log_i18n_profile"

    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    translations: Mapped[list[LogTranslationForLang]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )

    def get_translation_for_lang(
        self, lang: Lang | str
    ) -> LogTranslationForLang | None:
        return next((t for t in self.translations if t.lang == lang), None)

    def get_translation(self, lang: Lang | str, key_type: str, key: str) -> str | None:
        translation = self.get_translation_for_lang(lang)
        if not translation:
            translation = self.get_translation_for_lang(DEFAULT_LANG)

        if not translation:
            return None

        return translation.translation.get_translation(key_type, key)


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


class LogI18nProfileResponse(BaseModel, HasDatetimeSerialization):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = _ProfileIdField()
    name: str = _ProfileNameField()
    translations: dict[Lang, LogTranslation] = _ProfileTranslationsField(
        default_factory=dict
    )
    created_at: datetime = _ProfileCreatedAtField()

    @field_validator("translations", mode="before")
    def validate_translations(
        cls, translations: list[LogTranslation]
    ) -> dict[Lang, LogTranslation]:
        return {t.lang: t.translation for t in translations}


class LogI18nProfileListResponse(
    PagePaginatedResponse[LogI18nProfile, LogI18nProfileResponse]
):
    @classmethod
    def build_item(cls, profile: LogI18nProfile) -> LogI18nProfileResponse:
        return LogI18nProfileResponse.model_validate(profile)
