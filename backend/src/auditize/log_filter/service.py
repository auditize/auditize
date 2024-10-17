from uuid import UUID

from auditize.database import get_dbm
from auditize.exceptions import (
    UnknownModelException,
    ValidationError,
    enhance_constraint_violation_exception,
)
from auditize.log_filter.models import LogFilter, LogFilterUpdate
from auditize.repo.service import get_repo
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    update_resource_document,
)


async def _validate_log_filter(log_filter: LogFilter | LogFilterUpdate):
    # please note that we don't check if the user has the permission on the repo logs
    # the actual permission check is done when the user actually
    if log_filter.repo_id:
        try:
            await get_repo(log_filter.repo_id)
        except UnknownModelException:
            raise ValidationError(f"Repository {log_filter.repo_id!r} does not exist")


async def create_log_filter(log_filter: LogFilter) -> UUID:
    await _validate_log_filter(log_filter)
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_filter"
    ):
        return await create_resource_document(get_dbm().core_db.log_filters, log_filter)


def _log_filter_discriminator(user_id: UUID, log_filter_id: UUID) -> dict:
    return {"_id": log_filter_id, "user_id": user_id}


async def update_log_filter(
    user_id: UUID, log_filter_id: UUID, update: LogFilterUpdate
):
    await _validate_log_filter(update)
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_filter"
    ):
        await update_resource_document(
            get_dbm().core_db.log_filters,
            _log_filter_discriminator(user_id, log_filter_id),
            update,
        )


async def get_log_filter(user_id: UUID, log_filter_id: UUID) -> LogFilter:
    result = await get_resource_document(
        get_dbm().core_db.log_filters, _log_filter_discriminator(user_id, log_filter_id)
    )
    return LogFilter.model_validate(result)


async def get_log_filters(
    user_id: UUID, *, query: str, is_favorite: bool | None, page: int, page_size: int
) -> tuple[list[LogFilter], PagePaginationInfo]:
    doc_filter = {"user_id": user_id}
    if query:
        doc_filter["$text"] = {"$search": query}
    if is_favorite is not None:
        doc_filter["is_favorite"] = is_favorite
    results, page_info = await find_paginated_by_page(
        get_dbm().core_db.log_filters,
        filter=doc_filter,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )
    return [LogFilter.model_validate(result) async for result in results], page_info


async def delete_log_filter(user_id: UUID, log_filter_id: UUID):
    await delete_resource_document(
        get_dbm().core_db.log_filters, _log_filter_discriminator(user_id, log_filter_id)
    )


async def delete_log_filters_with_repo(repo_id: UUID):
    try:
        await delete_resource_document(
            get_dbm().core_db.log_filters, {"repo_id": repo_id}
        )
    except UnknownModelException:
        pass
