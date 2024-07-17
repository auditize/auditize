from auditize.database import DatabaseManager
from auditize.exceptions import UnknownModelException, ValidationError
from auditize.helpers.resources.service import create_resource_document
from auditize.logfilters.models import LogFilter
from auditize.repos.service import get_repo


async def _validate_log_filter(dbm: DatabaseManager, log_filter: LogFilter):
    # please note that we don't check if the user has the permission on the repo logs
    # the actual permission check is done when the user actually
    try:
        await get_repo(dbm, log_filter.repo_id)
    except UnknownModelException:
        raise ValidationError(f"Repo {log_filter.repo_id!r} does not exist")


async def create_log_filter(dbm: DatabaseManager, log_filter: LogFilter) -> str:
    await _validate_log_filter(dbm, log_filter)
    return await create_resource_document(dbm.core_db.log_filters, log_filter)
