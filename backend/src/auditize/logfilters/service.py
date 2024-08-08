from uuid import UUID

from auditize.database import DatabaseManager
from auditize.exceptions import UnknownModelException, ValidationError
from auditize.logfilters.models import LogFilter, LogFilterUpdate
from auditize.repos.service import get_repo
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    update_resource_document,
)


async def _validate_log_filter(
    dbm: DatabaseManager, log_filter: LogFilter | LogFilterUpdate
):
    # please note that we don't check if the user has the permission on the repo logs
    # the actual permission check is done when the user actually
    if log_filter.repo_id:
        try:
            await get_repo(dbm, log_filter.repo_id)
        except UnknownModelException:
            raise ValidationError(f"Repo {log_filter.repo_id!r} does not exist")


async def create_log_filter(dbm: DatabaseManager, log_filter: LogFilter) -> str:
    await _validate_log_filter(dbm, log_filter)
    return await create_resource_document(dbm.core_db.log_filters, log_filter)


def _log_filter_discriminator(user_id: UUID, log_filter_id) -> dict:
    return {"_id": UUID(log_filter_id), "user_id": user_id}


async def update_log_filter(
    dbm: DatabaseManager, user_id: UUID, log_filter_id: str, update: LogFilterUpdate
):
    await _validate_log_filter(dbm, update)
    await update_resource_document(
        dbm.core_db.log_filters,
        _log_filter_discriminator(user_id, log_filter_id),
        update,
    )


async def get_log_filter(
    dbm: DatabaseManager, user_id: UUID, log_filter_id: str
) -> LogFilter:
    result = await get_resource_document(
        dbm.core_db.log_filters, _log_filter_discriminator(user_id, log_filter_id)
    )
    return LogFilter.model_validate(result)


async def get_log_filters(
    dbm: DatabaseManager, user_id: UUID, query: str, page: int, page_size: int
) -> tuple[list[LogFilter], PagePaginationInfo]:
    doc_filter = {"user_id": user_id}
    if query:
        doc_filter["$text"] = {"$search": query}
    results, page_info = await find_paginated_by_page(
        dbm.core_db.log_filters,
        filter=doc_filter,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )
    return [LogFilter.model_validate(result) async for result in results], page_info


async def delete_log_filter(dbm: DatabaseManager, user_id: UUID, log_filter_id: str):
    await delete_resource_document(
        dbm.core_db.log_filters, _log_filter_discriminator(user_id, log_filter_id)
    )


async def delete_log_filters_with_repo(dbm: DatabaseManager, repo_id: str):
    try:
        await delete_resource_document(dbm.core_db.log_filters, {"repo_id": repo_id})
    except UnknownModelException:
        pass
