from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auditize.database.sql.models import HasDates, HasId, SqlModel
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile.models import LogLabels


class LogLabelsAsJSON(TypeDecorator):
    impl = JSON

    def process_bind_param(self, value: LogLabels, _) -> dict:
        # we use exclude_none=True instead of exclude_unset=True
        # to keep the potential empty dict fields in LogTranslation sub-model
        return value.model_dump(exclude_none=True)

    def process_result_value(self, value: dict, _) -> LogLabels:
        return LogLabels.model_validate(value)


class LogTranslation(SqlModel):
    __tablename__ = "log_i18n_profile_translation"

    id: Mapped[int] = mapped_column(primary_key=True)
    lang: Mapped[Lang] = mapped_column(String())
    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("log_i18n_profile.id", ondelete="CASCADE")
    )
    labels: Mapped[LogLabels] = mapped_column(LogLabelsAsJSON())


class LogI18nProfile(SqlModel, HasId, HasDates):
    __tablename__ = "log_i18n_profile"

    name: Mapped[str] = mapped_column(unique=True, index=True)
    translations: Mapped[list[LogTranslation]] = relationship(
        lazy="selectin", cascade="all, delete-orphan"
    )

    def get_translation(self, lang: Lang | str) -> LogTranslation | None:
        return next((t for t in self.translations if t.lang == lang), None)

    def translate(
        self, lang: Lang | str, category: str, key: str, enum_value: str | None = None
    ) -> str | None:
        from auditize.i18n.lang import DEFAULT_LANG

        translation = self.get_translation(lang)
        if not translation:
            translation = self.get_translation(DEFAULT_LANG)

        if not translation:
            return None

        return translation.labels.translate(category, key, enum_value)
