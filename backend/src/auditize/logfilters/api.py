from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.auth.authorizer import (
    Authorized,
)
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.helpers.pagination.page.api_models import PagePaginationParams
from auditize.helpers.resources.api_models import ResourceSearchParams
from auditize.logfilters import service
from auditize.logfilters.api_models import (
    LogFilterCreationRequest,
    LogFilterCreationResponse,
    LogFilterListResponse,
    LogFilterReadingResponse,
    LogFilterUpdateRequest,
)
from auditize.logfilters.models import LogFilter, LogFilterUpdate
from auditize.permissions.assertions import can_read_logs

router = APIRouter(responses=error_responses(401, 403))


@router.post(
    "/users/me/logs/filters",
    summary="Create log filter",
    tags=["log-filters"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_filter(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_logs()),
    log_filter: LogFilterCreationRequest,
) -> LogFilterCreationResponse:
    authenticated.ensure_user()
    log_filter_id = await service.create_log_filter(
        dbm,
        LogFilter.model_validate(
            {
                **log_filter.model_dump(),
                "user_id": authenticated.user.id,
            }
        ),
    )
    return LogFilterCreationResponse(id=log_filter_id)


@router.patch(
    "/users/me/logs/filters/{filter_id}",
    summary="Update log filter",
    tags=["log-filters"],
    status_code=204,
    responses=error_responses(400, 404, 409),
)
async def update_filter(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_logs()),
    update: LogFilterUpdateRequest,
    filter_id: str,
):
    authenticated.ensure_user()
    await service.update_log_filter(
        dbm,
        authenticated.user.id,
        filter_id,
        LogFilterUpdate.model_validate(update.model_dump(exclude_unset=True)),
    )


@router.get(
    "/users/me/logs/filters/{filter_id}",
    summary="Get log filter",
    tags=["log-filters"],
    status_code=200,
    responses=error_responses(404),
)
async def get_filter(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_logs()),
    filter_id: str,
) -> LogFilterReadingResponse:
    authenticated.ensure_user()
    log_filter = await service.get_log_filter(dbm, authenticated.user.id, filter_id)
    return LogFilterReadingResponse.model_validate(log_filter.model_dump())


@router.get(
    "/users/me/logs/filters",
    summary="List log filters",
    tags=["log-filters"],
)
async def list_log_filters(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_logs()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> LogFilterListResponse:
    authenticated.ensure_user()
    log_filters, page_info = await service.get_log_filters(
        dbm,
        user_id=authenticated.user.id,
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    return LogFilterListResponse.build(log_filters, page_info)


@router.delete(
    "/users/me/logs/filters/{filter_id}",
    summary="Delete log filter",
    tags=["log-filters"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_filter(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_logs()),
    filter_id: str,
):
    authenticated.ensure_user()
    await service.delete_log_filter(dbm, authenticated.user.id, filter_id)
