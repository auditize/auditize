from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from auditize.auth.authorizer import Authorized
from auditize.helpers.api.errors import error_responses
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile import service
from auditize.log_i18n_profile.models import (
    LogI18nProfileCreate,
    LogI18nProfileListResponse,
    LogI18nProfileResponse,
    LogI18nProfileUpdate,
    LogTranslation,
)
from auditize.permissions.assertions import (
    can_read_repo,
    can_write_repo,
)
from auditize.resource.api_models import ResourceSearchParams
from auditize.resource.pagination.page.api_models import PagePaginationParams

router = APIRouter(responses=error_responses(401, 403))


@router.post(
    "/log-i18n-profiles",
    summary="Create log i18n profile",
    description="Requires `repo:write` permission.",
    operation_id="create_log_i18n_profile",
    tags=["log-i18n-profile"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_profile(
    _: Authorized(can_write_repo()), profile_create: LogI18nProfileCreate
) -> LogI18nProfileResponse:
    return await service.create_log_i18n_profile(profile_create)


@router.patch(
    "/log-i18n-profiles/{profile_id}",
    summary="Update log i18n profile",
    description="Requires `repo:write` permission.",
    operation_id="update_log_i18n_profile",
    tags=["log-i18n-profile"],
    status_code=200,
    responses=error_responses(400, 409),
)
async def update_profile(
    _: Authorized(can_write_repo()), profile_id: UUID, update: LogI18nProfileUpdate
) -> LogI18nProfileResponse:
    return await service.update_log_i18n_profile(profile_id, update)


@router.get(
    "/log-i18n-profiles/{profile_id}",
    summary="Get log i18n profile",
    description="Requires `repo:read` permission.",
    operation_id="get_log_i18n_profile",
    tags=["log-i18n-profile"],
    responses=error_responses(404),
)
async def get_profile(
    _: Authorized(can_read_repo()), profile_id: UUID
) -> LogI18nProfileResponse:
    return await service.get_log_i18n_profile(profile_id)


@router.get(
    "/log-i18n-profiles/{profile_id}/translations/{lang}",
    summary="Get log i18n profile translation",
    description="Requires `repo:read` permission.",
    operation_id="get_log_i18n_profile_translation",
    tags=["log-i18n-profile"],
    responses=error_responses(404),
)
async def get_profile_translation(
    _: Authorized(can_read_repo()), profile_id: UUID, lang: Lang
) -> LogTranslation:
    return await service.get_log_i18n_profile_translation(profile_id, lang)


@router.get(
    "/log-i18n-profiles",
    summary="List log i18n profiles",
    description="Requires `repo:read` permission.",
    operation_id="list_log_i18n_profiles",
    tags=["log-i18n-profile"],
)
async def list_profiles(
    _: Authorized(can_read_repo()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> LogI18nProfileListResponse:
    profiles, page_info = await service.get_log_i18n_profiles(
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    return LogI18nProfileListResponse.build(profiles, page_info)


@router.delete(
    "/log-i18n-profiles/{profile_id}",
    summary="Delete log i18n profile",
    description="Requires `repo:write` permission.",
    operation_id="delete_log_i18n_profile",
    tags=["log-i18n-profile"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_profile(_: Authorized(can_write_repo()), profile_id: UUID):
    await service.delete_log_i18n_profile(profile_id)
