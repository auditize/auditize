from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.auth.authorizer import Authorized
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.helpers.pagination.page.api_models import PagePaginationParams
from auditize.helpers.resources.api_models import ResourceSearchParams
from auditize.logi18nprofiles import service
from auditize.logi18nprofiles.api_models import (
    LogI18nProfileCreationRequest,
    LogI18nProfileCreationResponse,
    LogI18nProfileListResponse,
    LogI18nProfileReadingResponse,
    LogI18nProfileUpdateRequest,
    LogTranslation,
)
from auditize.logi18nprofiles.models import LogI18nProfile, LogI18nProfileUpdate
from auditize.permissions.assertions import (
    can_read_repos,
    can_write_repos,
)
from auditize.users.models import Lang

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
        dbm,
        profile_id,
        # we use exclude_none=True instead of exclude_unset=True
        # to keep the potential empty dict fields in LogTranslation sub-model
        LogI18nProfileUpdate.model_validate(update.model_dump(exclude_none=True)),
    )


@router.get(
    "/log-i18n-profiles/{profile_id}",
    summary="Get log i18n profile",
    tags=["log-i18n-profiles"],
    responses=error_responses(404),
)
async def get_profile(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_repos()),
    profile_id: str,
) -> LogI18nProfileReadingResponse:
    profile = await service.get_log_i18n_profile(dbm, profile_id)
    return LogI18nProfileReadingResponse.model_validate(profile.model_dump())


@router.get(
    "/log-i18n-profiles/{profile_id}/translations/{lang}",
    summary="Get log i18n profile translation",
    tags=["log-i18n-profiles"],
    responses=error_responses(404),
)
async def get_profile_translation(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_repos()),
    profile_id: str,
    lang: Lang,
) -> LogTranslation:
    translation = await service.get_log_i18n_profile_translation(dbm, profile_id, lang)
    return LogTranslation.model_validate(translation.model_dump())


@router.get(
    "/log-i18n-profiles",
    summary="List log i18n profiles",
    tags=["log-i18n-profiles"],
)
async def list_profiles(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_repos()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> LogI18nProfileListResponse:
    profiles, page_info = await service.get_log_i18n_profiles(
        dbm,
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    return LogI18nProfileListResponse.build(profiles, page_info)


@router.delete(
    "/log-i18n-profiles/{profile_id}",
    summary="Delete log i18n profile",
    tags=["log-i18n-profiles"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_profile(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_repos()),
    profile_id: str,
):
    await service.delete_log_i18n_profile(dbm, profile_id)
