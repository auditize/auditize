from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.exception import error_responses
from auditize.auth.authorizer import (
    Authenticated,
    Require,
    RequireUser,
)
from auditize.dependencies import get_db_session
from auditize.log_filter import service
from auditize.log_filter.models import (
    LogFilterCreate,
    LogFilterListParams,
    LogFilterListResponse,
    LogFilterResponse,
    LogFilterUpdate,
)
from auditize.permissions.assertions import can_read_logs_from_any_repo

router = APIRouter(responses=error_responses(401, 403), tags=["internal"])


@router.post(
    "/users/me/logs/filters",
    summary="Create log filter",
    operation_id="create_log_filter",
    tags=["log-filter"],
    status_code=201,
    response_model=LogFilterResponse,
    responses=error_responses(400, 409),
)
async def create_filter(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[
        Authenticated, Depends(RequireUser(can_read_logs_from_any_repo()))
    ],
    log_filter: LogFilterCreate,
):
    return await service.create_log_filter(session, authorized.user.id, log_filter)


@router.patch(
    "/users/me/logs/filters/{filter_id}",
    summary="Update log filter",
    operation_id="update_log_filter",
    tags=["log-filter"],
    status_code=200,
    response_model=LogFilterResponse,
    responses=error_responses(400, 404, 409),
)
async def update_filter(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[
        Authenticated, Depends(RequireUser(can_read_logs_from_any_repo()))
    ],
    update: LogFilterUpdate,
    filter_id: UUID,
):
    return await service.update_log_filter(
        session, authorized.user.id, filter_id, update
    )


@router.get(
    "/users/me/logs/filters/{filter_id}",
    summary="Get log filter",
    operation_id="get_log_filter",
    tags=["log-filter"],
    status_code=200,
    response_model=LogFilterResponse,
    responses=error_responses(404),
)
async def get_filter(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[
        Authenticated, Depends(Require(can_read_logs_from_any_repo()))
    ],
    filter_id: UUID,
):
    return await service.get_log_filter(session, authorized.user.id, filter_id)


@router.get(
    "/users/me/logs/filters",
    summary="List log filters",
    operation_id="list_log_filters",
    tags=["log-filter"],
    response_model=LogFilterListResponse,
)
async def list_log_filters(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[
        Authenticated, Depends(Require(can_read_logs_from_any_repo()))
    ],
    params: Annotated[LogFilterListParams, Query()],
):
    log_filters, page_info = await service.get_log_filters(
        session,
        user_id=authorized.user.id,
        query=params.query,
        is_favorite=params.is_favorite,
        page=params.page,
        page_size=params.page_size,
    )
    return LogFilterListResponse.build(log_filters, page_info)


@router.delete(
    "/users/me/logs/filters/{filter_id}",
    summary="Delete log filter",
    operation_id="delete_log_filter",
    tags=["log-filter"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_filter(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[
        Authenticated, Depends(Require(can_read_logs_from_any_repo()))
    ],
    filter_id: UUID,
):
    await service.delete_log_filter(session, authorized.user.id, filter_id)
