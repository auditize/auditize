from uuid import UUID

from auditize.database import get_core_db
from auditize.exceptions import (
    ConstraintViolation,
    enhance_constraint_violation_exception,
)
from auditize.log_i18n_profile.models import (
    LogI18nProfile,
    LogI18nProfileCreate,
    LogI18nProfileRead,
    LogI18nProfileUpdate,
    LogTranslation,
)
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    create_resource_document2,
    delete_resource_document,
    get_resource_document,
    has_resource_document,
    update_resource_document,
)


async def create_log_i18n_profile(
    profile_create: LogI18nProfileCreate,
) -> LogI18nProfile:
    profile = LogI18nProfile.model_validate(profile_create.model_dump())
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_i18n_profile"
    ):
        profile_data = await create_resource_document2(
            get_core_db().log_i18n_profiles, profile
        )
    return LogI18nProfile.model_validate(profile_data)


async def update_log_i18n_profile(
    profile_id: UUID, profile_update: LogI18nProfileUpdate
) -> LogI18nProfile:
    profile = await get_log_i18n_profile(profile_id)
    if profile_update.name:
        profile.name = profile_update.name
    if profile_update.translations:
        for lang, translation in profile_update.translations.items():
            if translation:
                profile.translations[lang] = translation
            else:
                # NB: lang is not necessarily present in existing translations
                profile.translations.pop(lang, None)

    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_i18n_profile"
    ):
        # we use exclude_none=True instead of exclude_unset=True
        # to keep the potential empty dict fields in LogTranslation sub-model
        profile_data = profile.model_dump(exclude_none=True, exclude={"id"})
        await update_resource_document(
            get_core_db().log_i18n_profiles, profile_id, profile_data
        )

    return await get_log_i18n_profile(profile_id)


async def get_log_i18n_profile(profile_id: UUID) -> LogI18nProfile:
    result = await get_resource_document(get_core_db().log_i18n_profiles, profile_id)
    return LogI18nProfile.model_validate(result)


async def get_log_i18n_profile_translation(
    profile_id: UUID, lang: str
) -> LogTranslation:
    result = await get_resource_document(
        get_core_db().log_i18n_profiles,
        profile_id,
        projection={"translations." + lang: 1},
    )
    if lang in result["translations"]:
        return LogTranslation.model_validate(result["translations"][lang])
    else:
        return LogTranslation()


async def get_log_i18n_profiles(
    query: str, page: int, page_size: int
) -> tuple[list[LogI18nProfile], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        get_core_db().log_i18n_profiles,
        filter={"$text": {"$search": query}} if query else None,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )

    return [
        LogI18nProfile.model_validate(result) async for result in results
    ], page_info


async def delete_log_i18n_profile(profile_id: UUID):
    # NB: workaround circular import
    from auditize.repo.service import is_log_i18n_profile_used_by_repo

    if await is_log_i18n_profile_used_by_repo(profile_id):
        raise ConstraintViolation(
            ("error.log_i18n_profile_deletion_forbidden", {"profile_id": profile_id}),
        )
    await delete_resource_document(get_core_db().log_i18n_profiles, profile_id)


async def has_log_i18n_profile(profile_id: UUID) -> bool:
    return await has_resource_document(get_core_db().log_i18n_profiles, profile_id)
