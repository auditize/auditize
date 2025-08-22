from sqlalchemy import JSON, ForeignKey, TypeDecorator, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.dbm import Base
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile.models import LogTranslation
from auditize.resource.sql_models import HasCreatedAt, HasId


class LogTranslationAsJSON(TypeDecorator):
    impl = JSON

    def process_bind_param(self, value: LogTranslation, _) -> dict:
        # we use exclude_none=True instead of exclude_unset=True
        # to keep the potential empty dict fields in LogTranslation sub-model
        return value.model_dump(exclude_none=True)

    def process_result_value(self, value: dict, _) -> LogTranslation:
        return LogTranslation.model_validate(value)


class LogTranslationForLang(Base):
    __tablename__ = "log_i18n_profile_translation"

    id: Mapped[int] = mapped_column(primary_key=True)
    lang: Mapped[Lang] = mapped_column(nullable=False)
    profile_id: Mapped[Uuid] = mapped_column(
        ForeignKey("log_i18n_profile.id", ondelete="CASCADE"), nullable=False
    )
    translation: Mapped[LogTranslation] = mapped_column(
        LogTranslationAsJSON(), nullable=False
    )


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
        from auditize.i18n.lang import DEFAULT_LANG

        translation = self.get_translation_for_lang(lang)
        if not translation:
            translation = self.get_translation_for_lang(DEFAULT_LANG)

        if not translation:
            return None

        return translation.translation.get_translation(key_type, key)
