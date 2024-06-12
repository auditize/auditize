from auditize.database import DatabaseManager
from auditize.helpers.resources.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    update_resource_document,
)
from auditize.logi18nprofiles.models import LogI18nProfile


async def create_log_i18n_profile(dbm: DatabaseManager, profile: LogI18nProfile) -> str:
    profile_id = await create_resource_document(dbm.core_db.logi18nprofiles, profile)
    return profile_id
