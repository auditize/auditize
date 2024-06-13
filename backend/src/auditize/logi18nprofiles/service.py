from auditize.database import DatabaseManager
from auditize.helpers.pagination.page.models import PagePaginationInfo
from auditize.helpers.pagination.page.service import find_paginated_by_page
from auditize.helpers.resources.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    update_resource_document,
)
from auditize.logi18nprofiles.models import LogI18nProfile, LogI18nProfileUpdate


async def create_log_i18n_profile(dbm: DatabaseManager, profile: LogI18nProfile) -> str:
    profile_id = await create_resource_document(dbm.core_db.logi18nprofiles, profile)
    return profile_id


async def update_log_i18n_profile(
    dbm: DatabaseManager, profile_id: str, update: LogI18nProfileUpdate
):
    profile = await get_log_i18n_profile(dbm, profile_id)
    if update.name:
        profile.name = update.name
    if update.translations:
        for lang, translation in update.translations.items():
            if translation:
                profile.translations[lang] = translation
            else:
                # NB: lang is not necessarily present in existing translations
                profile.translations.pop(lang, None)

    await update_resource_document(dbm.core_db.logi18nprofiles, profile_id, profile)


async def get_log_i18n_profile(dbm: DatabaseManager, profile_id: str) -> LogI18nProfile:
    result = await get_resource_document(dbm.core_db.logi18nprofiles, profile_id)
    return LogI18nProfile.model_validate(result)


async def get_log_i18n_profiles(
    dbm: DatabaseManager, query: str, page: int, page_size: int
) -> tuple[list[LogI18nProfile], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.logi18nprofiles,
        filter={"$text": {"$search": query}} if query else None,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )

    return [
        LogI18nProfile.model_validate(result) async for result in results
    ], page_info


async def delete_log_i18n_profile(dbm: DatabaseManager, profile_id: str):
    await delete_resource_document(dbm.core_db.logi18nprofiles, profile_id)
