from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.models.page_pagination import PagePaginationInfo
from auditize.database.sql.service import (
    delete_sql_model,
    find_paginated_by_page,
    get_sql_model,
    save_sql_model,
)
from auditize.exceptions import (
    ConstraintViolation,
    NotFoundError,
)
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile.models import (
    LogI18nProfileCreate,
    LogI18nProfileUpdate,
    LogLabels,
)
from auditize.log_i18n_profile.sql_models import (
    LogI18nProfile,
    LogTranslation,
)


def build_log_i18n_profile_constraint_rules(
    profile: LogI18nProfileCreate | LogI18nProfileUpdate,
) -> dict[str, Exception]:
    return {
        "ix_log_i18n_profile_name": ConstraintViolation(
            ("error.constraint_violation.log_i18n_profile", {"name": profile.name}),
        ),
    }


async def create_log_i18n_profile(
    session: AsyncSession,
    profile_create: LogI18nProfileCreate,
) -> LogI18nProfile:
    profile = LogI18nProfile(name=profile_create.name)
    for lang, labels in profile_create.translations.items():
        profile.translations.append(LogTranslation(lang=lang, labels=labels))

    await save_sql_model(
        session,
        profile,
        constraint_rules=build_log_i18n_profile_constraint_rules(profile_create),
    )

    return profile


async def update_log_i18n_profile(
    session: AsyncSession, profile_id: UUID, profile_update: LogI18nProfileUpdate
) -> LogI18nProfile:
    profile = await get_log_i18n_profile(session, profile_id)
    if profile_update.name:
        profile.name = profile_update.name
    if profile_update.translations:
        for lang, updated_labels in profile_update.translations.items():
            current_translation = profile.get_translation(lang)
            # Update or add translation for the specified lang
            if updated_labels:
                if current_translation:
                    current_translation.labels = updated_labels
                else:
                    profile.translations.append(
                        LogTranslation(lang=lang, labels=updated_labels)
                    )
            # Remove translation for the specified lang if it is None
            else:
                if current_translation:
                    profile.translations.remove(current_translation)

    await save_sql_model(
        session,
        profile,
        constraint_rules=build_log_i18n_profile_constraint_rules(profile_update),
    )

    return profile


async def get_log_i18n_profile(
    session: AsyncSession, profile_id: UUID
) -> LogI18nProfile:
    return await get_sql_model(session, LogI18nProfile, profile_id)


async def get_log_i18n_profile_translation(
    session: AsyncSession, profile_id: UUID, lang: str
) -> LogLabels:
    profile = await get_log_i18n_profile(session, profile_id)
    translation = profile.get_translation(lang)
    if translation:
        return translation.labels
    else:
        # Return an empty LogTranslation if no translation is found
        return LogLabels()


async def get_log_i18n_profiles(
    session: AsyncSession, query: str, page: int, page_size: int
) -> tuple[list[LogI18nProfile], PagePaginationInfo]:
    models, page_info = await find_paginated_by_page(
        session,
        LogI18nProfile,
        filter=LogI18nProfile.name.ilike(f"%{query}%") if query else None,
        order_by=LogI18nProfile.name.asc(),
        page=page,
        page_size=page_size,
    )
    return models, page_info


async def delete_log_i18n_profile(session: AsyncSession, profile_id: UUID):
    # NB: workaround circular import
    from auditize.repo.service import is_log_i18n_profile_used_by_repo

    if await is_log_i18n_profile_used_by_repo(session, profile_id):
        raise ConstraintViolation(
            ("error.log_i18n_profile_deletion_forbidden", {"profile_id": profile_id}),
        )
    await delete_sql_model(session, LogI18nProfile, profile_id)


async def has_log_i18n_profile(session: AsyncSession, profile_id: UUID) -> bool:
    try:
        await get_sql_model(session, LogI18nProfile, profile_id)
        return True
    except NotFoundError:
        return False


def _build_default_translation(value: str) -> str:
    return " ".join(s.capitalize() for s in value.split("-"))


def translate(
    profile: LogI18nProfile | None,
    lang: Lang | str,
    category: str,
    key: str,
    enum_value: str | None = None,
) -> str:
    label = None
    if profile:
        label = profile.translate(lang, category, key, enum_value)
    return (
        label
        if label
        else _build_default_translation(enum_value if enum_value is not None else key)
    )
