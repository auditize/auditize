from auditize.database import DatabaseManager
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
    doc_update = update.model_dump(exclude={"translations"}, exclude_none=True)
    if update.translations:
        for lang, translation in update.translations.items():
            doc_update[f"translations.{lang.value}"] = translation.model_dump()
    await update_resource_document(dbm.core_db.logi18nprofiles, profile_id, doc_update)
