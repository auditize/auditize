from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.auth.authorizer import Authorized
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.logi18nprofiles import service
from auditize.logi18nprofiles.api_models import (
    LogI18nProfileCreationRequest,
    LogI18nProfileCreationResponse,
)
from auditize.logi18nprofiles.models import LogI18nProfile
from auditize.permissions.assertions import (
    can_write_repos,
)

router = APIRouter(responses=error_responses(401, 403))


@router.post(
    "/log-i18n-profiles",
    summary="Create log i18n profile",
    tags=["log-i18n-profiles"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_profile(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_repos()),
    profile: LogI18nProfileCreationRequest,
) -> LogI18nProfileCreationResponse:
    profile_id = await service.create_log_i18n_profile(
        dbm, LogI18nProfile.model_validate(profile.model_dump())
    )

    return LogI18nProfileCreationResponse(id=profile_id)
