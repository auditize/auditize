from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from auditize.auth.authorizer import AuthorizedUser
from auditize.helpers.api.errors import error_responses
from auditize.log_filter import service
from auditize.log_filter.api_models import (
    LogFilterCreationRequest,
    LogFilterCreationResponse,
    LogFilterListResponse,
    LogFilterReadingResponse,
    LogFilterUpdateRequest,
)
from auditize.log_filter.models import LogFilter, LogFilterUpdate
from auditize.permissions.assertions import can_read_logs
from auditize.resource.api_models import ResourceSearchParams
from auditize.resource.pagination.page.api_models import PagePaginationParams

router = APIRouter(responses=error_responses(401, 403), tags=["internal"])


@router.post(
    "/users/me/logs/filters",
    summary="Create log filter",
    operation_id="create_log_filter",
    tags=["log-filter"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_filter(
    authorized: AuthorizedUser(can_read_logs()),
    log_filter: LogFilterCreationRequest,
) -> LogFilterCreationResponse:
    log_filter_id = await service.create_log_filter(
        LogFilter.model_validate(
            {
                **log_filter.model_dump(),
                "user_id": authorized.user.id,
            }
        ),
    )
    return LogFilterCreationResponse(id=log_filter_id)


@router.patch(
    "/users/me/logs/filters/{filter_id}",
    summary="Update log filter",
    operation_id="update_log_filter",
    tags=["log-filter"],
    status_code=204,
    responses=error_responses(400, 404, 409),
)
async def update_filter(
    authorized: AuthorizedUser(can_read_logs()),
    update: LogFilterUpdateRequest,
    filter_id: UUID,
):
    await service.update_log_filter(
        authorized.user.id,
        filter_id,
        LogFilterUpdate.model_validate(update.model_dump(exclude_unset=True)),
    )


@router.get(
    "/users/me/logs/filters/{filter_id}",
    summary="Get log filter",
    operation_id="get_log_filter",
    tags=["log-filter"],
    status_code=200,
    responses=error_responses(404),
)
async def get_filter(
    authorized: AuthorizedUser(can_read_logs()),
    filter_id: UUID,
) -> LogFilterReadingResponse:
    log_filter = await service.get_log_filter(authorized.user.id, filter_id)
    return LogFilterReadingResponse.model_validate(log_filter.model_dump())


@router.get(
    "/users/me/logs/filters",
    summary="List log filters",
    operation_id="list_log_filters",
    tags=["log-filter"],
)
async def list_log_filters(
    authorized: AuthorizedUser(can_read_logs()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    is_favorite: bool = None,
    page_params: Annotated[PagePaginationParams, Depends()] = PagePaginationParams(),
) -> LogFilterListResponse:
    log_filters, page_info = await service.get_log_filters(
        user_id=authorized.user.id,
        query=search_params.query,
        is_favorite=is_favorite,
        page=page_params.page,
        page_size=page_params.page_size,
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
    authorized: AuthorizedUser(can_read_logs()),
    filter_id: UUID,
):
    await service.delete_log_filter(authorized.user.id, filter_id)
