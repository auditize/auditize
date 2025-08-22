from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.exceptions import (
    UnknownModelException,
    ValidationError,
    enhance_constraint_violation_exception,
)
from auditize.log_filter.models import LogFilterCreate, LogFilterUpdate
from auditize.log_filter.sql_models import LogFilter
from auditize.repo.service import get_repo
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.sql_service import find_paginated_by_page
from auditize.resource.sql_service import (
    delete_sql_model,
    get_sql_model,
    save_sql_model,
    update_sql_model,
)


async def _validate_log_filter(
    session: AsyncSession, log_filter: LogFilter | LogFilterUpdate
):
    # please note that we don't check if the user has the permission on the repo logs
    # the actual permission check is done when the user actually
    if log_filter.repo_id:
        try:
            await get_repo(session, log_filter.repo_id)
        except UnknownModelException:
            raise ValidationError(f"Repository {log_filter.repo_id!r} does not exist")


async def create_log_filter(
    session: AsyncSession, user_id: UUID, log_filter_create: LogFilterCreate
) -> LogFilter:
    await _validate_log_filter(session, log_filter_create)
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_filter"
    ):
        log_filter = LogFilter(
            name=log_filter_create.name,
            repo_id=log_filter_create.repo_id,
            user_id=user_id,
            search_params=log_filter_create.search_params,
            columns=log_filter_create.columns,
            is_favorite=log_filter_create.is_favorite,
        )
        await save_sql_model(session, log_filter)
    return log_filter


def _log_filter_filter(user_id: UUID, log_filter_id: UUID) -> Any:
    return and_(
        LogFilter.user_id == user_id,
        LogFilter.id == log_filter_id,
    )


async def update_log_filter(
    session: AsyncSession, user_id: UUID, log_filter_id: UUID, update: LogFilterUpdate
) -> LogFilter:
    await _validate_log_filter(session, update)
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_filter"
    ):
        log_filter = await get_log_filter(session, user_id, log_filter_id)
        await update_sql_model(session, log_filter, update)
    return await get_log_filter(session, user_id, log_filter_id)


async def get_log_filter(
    session: AsyncSession, user_id: UUID, log_filter_id: UUID
) -> LogFilter:
    return await get_sql_model(
        session, LogFilter, _log_filter_filter(user_id, log_filter_id)
    )


async def get_log_filters(
    session: AsyncSession,
    user_id: UUID,
    *,
    query: str,
    is_favorite: bool | None,
    page: int,
    page_size: int,
) -> tuple[list[LogFilter], PagePaginationInfo]:
    filter = LogFilter.user_id == user_id
    if query:
        filter = and_(filter, LogFilter.name.ilike(f"%{query}%"))
    if is_favorite is not None:
        filter = and_(filter, LogFilter.is_favorite == is_favorite)
    results, page_info = await find_paginated_by_page(
        session,
        LogFilter,
        filter=filter,
        order_by=LogFilter.name.asc(),
        page=page,
        page_size=page_size,
    )
    return results, page_info


async def delete_log_filter(session: AsyncSession, user_id: UUID, log_filter_id: UUID):
    await delete_sql_model(
        session, LogFilter, _log_filter_filter(user_id, log_filter_id)
    )


async def delete_log_filters_with_repo(session: AsyncSession, repo_id: UUID):
    await session.execute(delete(LogFilter).where(LogFilter.repo_id == repo_id))
    await session.commit()
