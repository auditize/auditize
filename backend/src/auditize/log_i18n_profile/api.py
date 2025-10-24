from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.exception import error_responses
from auditize.api.models.search import PagePaginatedSearchParams
from auditize.auth.authorizer import Authenticated, Require
from auditize.dependencies import get_db_session
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile import service
from auditize.log_i18n_profile.models import (
    LogI18nProfileCreate,
    LogI18nProfileListResponse,
    LogI18nProfileResponse,
    LogI18nProfileUpdate,
    LogLabels,
)
from auditize.permissions.assertions import (
    can_read_repo,
    can_write_repo,
)

router = APIRouter(
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
)


@router.post(
    "/log-i18n-profiles",
    summary="Create log i18n profile",
    description="Requires `repo:write` permission.",
    operation_id="create_log_i18n_profile",
    tags=["log-i18n-profile"],
    status_code=status.HTTP_201_CREATED,
    response_model=LogI18nProfileResponse,
    responses=error_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT),
)
async def create_profile(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_write_repo()))],
    profile_create: LogI18nProfileCreate,
):
    return await service.create_log_i18n_profile(session, profile_create)


@router.patch(
    "/log-i18n-profiles/{profile_id}",
    summary="Update log i18n profile",
    description="Requires `repo:write` permission.",
    operation_id="update_log_i18n_profile",
    tags=["log-i18n-profile"],
    status_code=status.HTTP_200_OK,
    response_model=LogI18nProfileResponse,
    responses=error_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT),
)
async def update_profile(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_write_repo()))],
    profile_id: UUID,
    update: LogI18nProfileUpdate,
):
    return await service.update_log_i18n_profile(session, profile_id, update)


@router.get(
    "/log-i18n-profiles/{profile_id}",
    summary="Get log i18n profile",
    description="Requires `repo:read` permission.",
    operation_id="get_log_i18n_profile",
    tags=["log-i18n-profile"],
    response_model=LogI18nProfileResponse,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_profile(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_repo()))],
    profile_id: UUID,
):
    return await service.get_log_i18n_profile(session, profile_id)


@router.get(
    "/log-i18n-profiles/{profile_id}/translations/{lang}",
    summary="Get log i18n profile translation",
    description="Requires `repo:read` permission.",
    operation_id="get_log_i18n_profile_translation",
    tags=["log-i18n-profile"],
    response_model=LogLabels,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_profile_translation(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_repo()))],
    profile_id: UUID,
    lang: Lang,
):
    return await service.get_log_i18n_profile_translation(session, profile_id, lang)


@router.get(
    "/log-i18n-profiles",
    summary="List log i18n profiles",
    description="Requires `repo:read` permission.",
    operation_id="list_log_i18n_profiles",
    tags=["log-i18n-profile"],
    response_model=LogI18nProfileListResponse,
)
async def list_profiles(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_repo()))],
    params: Annotated[PagePaginatedSearchParams, Query()],
):
    profiles, page_info = await service.get_log_i18n_profiles(
        session, params.query, params.page, params.page_size
    )
    return LogI18nProfileListResponse.build(profiles, page_info)


@router.delete(
    "/log-i18n-profiles/{profile_id}",
    summary="Delete log i18n profile",
    description="Requires `repo:write` permission.",
    operation_id="delete_log_i18n_profile",
    tags=["log-i18n-profile"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def delete_profile(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_write_repo()))],
    profile_id: UUID,
):
    await service.delete_log_i18n_profile(session, profile_id)
