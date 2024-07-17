from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.auth.authorizer import (
    Authorized,
)
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.logfilters import service
from auditize.logfilters.api_models import (
    LogFilterCreationRequest,
    LogFilterCreationResponse,
)
from auditize.logfilters.models import LogFilter
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
