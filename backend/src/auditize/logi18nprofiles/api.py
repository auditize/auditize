from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.auth.authorizer import Authorized
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.logi18nprofiles import service
from auditize.logi18nprofiles.api_models import (
    LogI18nProfileCreationRequest,
    LogI18nProfileCreationResponse,
    LogI18nProfileReadingResponse,
    LogI18nProfileUpdateRequest,
)
from auditize.logi18nprofiles.models import LogI18nProfile, LogI18nProfileUpdate
from auditize.permissions.assertions import (
    can_read_repos,
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


@router.patch(
    "/log-i18n-profiles/{profile_id}",
    summary="Update log i18n profile",
    tags=["log-i18n-profiles"],
    status_code=204,
    responses=error_responses(400, 409),
)
async def update_profile(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_repos()),
    profile_id: str,
    update: LogI18nProfileUpdateRequest,
):
    await service.update_log_i18n_profile(
        dbm, profile_id, LogI18nProfileUpdate.model_validate(update.model_dump())
    )


@router.get(
    "/log-i18n-profiles/{profile_id}",
    summary="Get log i18n profile",
    tags=["log-i18n-profiles"],
    responses=error_responses(404),
)
async def get_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_repos()),
    profile_id: str,
) -> LogI18nProfileReadingResponse:
    profile = await service.get_log_i18n_profile(dbm, profile_id)
    return LogI18nProfileReadingResponse.model_validate(profile.model_dump())
