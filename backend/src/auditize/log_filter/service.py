from typing import Any
from uuid import UUID

from sqlalchemy import and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.models.page_pagination import PagePaginationInfo
from auditize.database.sql.service import (
    delete_sql_model,
    find_paginated_by_page,
    get_sql_model,
    save_sql_model,
    update_sql_model,
)
from auditize.exceptions import (
    ConstraintViolation,
    ValidationError,
)
from auditize.log_filter.models import LogFilterCreate, LogFilterUpdate
from auditize.log_filter.sql_models import LogFilter


def _build_log_filter_constraint_rules(
    log_filter: LogFilterCreate | LogFilterUpdate,
) -> dict[str, Exception]:
    return {
        "ix_log_filter_name": ConstraintViolation(
            ("error.constraint_violation.log_filter", {"name": log_filter.name}),
        ),
        "fk_log_filter_repo_id": ValidationError(
            f"Repository {log_filter.repo_id!r} does not exist",
        ),
    }


async def create_log_filter(
    session: AsyncSession, user_id: UUID, log_filter_create: LogFilterCreate
) -> LogFilter:
    log_filter = LogFilter(
        name=log_filter_create.name,
        repo_id=log_filter_create.repo_id,
        user_id=user_id,
        search_params=log_filter_create.search_params,
        columns=log_filter_create.columns,
        is_favorite=log_filter_create.is_favorite,
    )
    await save_sql_model(
        session,
        log_filter,
        constraint_rules=_build_log_filter_constraint_rules(log_filter_create),
    )
    return log_filter


def _log_filter_filter(user_id: UUID, log_filter_id: UUID) -> Any:
    return and_(
        LogFilter.user_id == user_id,
        LogFilter.id == log_filter_id,
    )


async def update_log_filter(
    session: AsyncSession, user_id: UUID, log_filter_id: UUID, update: LogFilterUpdate
) -> LogFilter:
    log_filter = await get_log_filter(session, user_id, log_filter_id)
    await update_sql_model(
        session,
        log_filter,
        update,
        constraint_rules=_build_log_filter_constraint_rules(update),
    )
    return log_filter


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
