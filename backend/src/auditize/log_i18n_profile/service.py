from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from auditize.exceptions import (
    ConstraintViolation,
    UnknownModelException,
    enhance_constraint_violation_exception,
)
from auditize.log_i18n_profile.models import (
    LogI18nProfileCreate,
    LogI18nProfileUpdate,
    LogTranslation,
)
from auditize.log_i18n_profile.sql_models import (
    LogI18nProfile,
    LogTranslationForLang,
)
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.sql_service import find_paginated_by_page
from auditize.resource.sql_service import (
    delete_sql_model,
    get_sql_model,
    save_sql_model,
)


async def _save_log_i18n_profile(session: AsyncSession, profile: LogI18nProfile):
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_i18n_profile"
    ):
        await save_sql_model(session, profile)


async def create_log_i18n_profile(
    session: AsyncSession,
    profile_create: LogI18nProfileCreate,
) -> LogI18nProfile:
    profile = LogI18nProfile(name=profile_create.name)
    for translation_lang, translation in profile_create.translations.items():
        profile.translations.append(
            LogTranslationForLang(lang=translation_lang, translation=translation)
        )

    await _save_log_i18n_profile(session, profile)

    return profile


async def update_log_i18n_profile(
    session: AsyncSession, profile_id: UUID, profile_update: LogI18nProfileUpdate
) -> LogI18nProfile:
    profile = await get_log_i18n_profile(session, profile_id)
    if profile_update.name:
        profile.name = profile_update.name
    if profile_update.translations:
        for lang, updated_translation in profile_update.translations.items():
            current_translation = profile.get_translation_for_lang(lang)
            # Update or add translation for the specified lang
            if updated_translation:
                if current_translation:
                    current_translation.translation = updated_translation
                else:
                    profile.translations.append(
                        LogTranslationForLang(
                            lang=lang, translation=updated_translation
                        )
                    )
            # Remove translation for the specified lang if it is None
            else:
                if current_translation:
                    profile.translations.remove(current_translation)

    await _save_log_i18n_profile(session, profile)

    return profile


async def get_log_i18n_profile(
    session: AsyncSession, profile_id: UUID
) -> LogI18nProfile:
    return await get_sql_model(session, LogI18nProfile, profile_id)


async def get_log_i18n_profile_translation(
    session: AsyncSession, profile_id: UUID, lang: str
) -> LogTranslation:
    profile = await get_log_i18n_profile(session, profile_id)
    translation = profile.get_translation_for_lang(lang)
    if translation:
        return translation.translation
    else:
        # Return an empty LogTranslation if no translation is found
        return LogTranslation()


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
    except UnknownModelException:
        return False
