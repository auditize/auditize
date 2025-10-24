from enum import Enum
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.exception import error_responses
from auditize.apikey.models import ApikeyUpdate
from auditize.apikey.service import update_apikey
from auditize.auth.authorizer import (
    Authenticated,
    Require,
    RequireLogReadPermission,
    RequireUser,
)
from auditize.dependencies import get_db_session
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile.models import LogLabels
from auditize.permissions.assertions import (
    can_read_logs_from_all_repos,
    can_read_logs_from_repo,
    can_read_repo,
    can_write_logs_to_all_repos,
    can_write_logs_to_repo,
    can_write_repo,
    permissions_and,
)
from auditize.permissions.models import (
    LogPermissionsInput,
    PermissionsInput,
    RepoLogPermissionsInput,
)
from auditize.repo import service
from auditize.repo.models import (
    RepoCreate,
    RepoIncludeOptions,
    RepoListParams,
    RepoListResponse,
    RepoResponse,
    RepoStats,
    RepoStatus,
    RepoUpdate,
    RepoWithStatsResponse,
    UserRepoListParams,
    UserRepoListResponse,
    UserRepoPermissions,
)
from auditize.user.models import UserUpdate
from auditize.user.service import update_user

router = APIRouter(
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
)


@router.post(
    "/repos",
    summary="Create log repository",
    description="Requires `repo:write` permission.",
    operation_id="create_repo",
    tags=["repo"],
    status_code=status.HTTP_201_CREATED,
    response_model=RepoResponse,
    responses=error_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT),
)
async def create_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_repo()))],
    repo_create: RepoCreate,
):
    repo = await service.create_repo(session, repo_create)

    # Ensure that authorized will have read & write logs permissions on the repo he created
    if not authorized.comply(
        permissions_and(can_read_logs_from_all_repos(), can_write_logs_to_all_repos())
    ):
        grant_rw_on_repo_logs = PermissionsInput(
            logs=LogPermissionsInput(
                repos=[RepoLogPermissionsInput(repo_id=repo.id, read=True, write=True)]
            ),
        )
        if authorized.apikey:
            await update_apikey(
                session,
                authorized.apikey.id,
                ApikeyUpdate(permissions=grant_rw_on_repo_logs),
            )
        if authorized.user:
            await update_user(
                session,
                authorized.user.id,
                UserUpdate(permissions=grant_rw_on_repo_logs),
            )
    return repo


@router.patch(
    "/repos/{repo_id}",
    summary="Update log repository",
    description="Requires `repo:write` permission.",
    operation_id="update_repo",
    tags=["repo"],
    status_code=status.HTTP_200_OK,
    response_model=RepoResponse,
    responses=error_responses(
        status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT
    ),
)
async def update_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_write_repo()))],
    repo_id: UUID,
    update: RepoUpdate,
):
    return await service.update_repo(session, repo_id, update)


async def _handle_repo_include_options(
    session: AsyncSession, repo_read: RepoResponse, include: list[RepoIncludeOptions]
):
    if RepoIncludeOptions.STATS in include:
        stats = await service.get_repo_stats(session, repo_read.id)
        repo_read.stats = RepoStats.model_validate(stats.model_dump())


@router.get(
    "/repos/{repo_id}",
    summary="Get log repository",
    description="Requires `repo:read` permission.",
    tags=["repo"],
    response_model=RepoWithStatsResponse,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_repo()))],
    repo_id: UUID,
    include: Annotated[list[RepoIncludeOptions], Query()] = (),
):
    repo = await service.get_repo(session, repo_id)
    response = RepoWithStatsResponse.from_repo(repo)
    await _handle_repo_include_options(session, response, include)
    return response


@router.get(
    "/repos/{repo_id}/translation",
    summary="Get log repository translation for the authenticated user",
    description="Requires `log:read` permission.",
    operation_id="get_repo_translation_for_user",
    tags=["repo", "internal"],
    response_model=LogLabels,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_repo_translation_for_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
):
    authorized.ensure_user()
    return await service.get_repo_translation(session, repo_id, authorized.user.lang)


@router.get(
    "/repos/{repo_id}/translations/{lang}",
    summary="Get log repository translation",
    description="Requires `log:read` permission.",
    operation_id="get_repo_translation",
    tags=["repo"],
    response_model=LogLabels,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_repo_translation(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    lang: Lang,
):
    return await service.get_repo_translation(session, repo_id, lang)


@router.get(
    "/repos",
    summary="List log repositories",
    description="Requires `repo:read` permission.",
    operation_id="list_repos",
    tags=["repo"],
    response_model=RepoListResponse,
)
async def list_repos(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_repo()))],
    params: Annotated[RepoListParams, Query()],
):
    repos, page_info = await service.get_repos(
        session,
        query=params.query,
        page=params.page,
        page_size=params.page_size,
    )
    repo_list = RepoListResponse.build(repos, page_info)
    for repo_read in repo_list.items:
        await _handle_repo_include_options(session, repo_read, params.include)
    return repo_list


@router.get(
    "/users/me/repos",
    summary="List user accessible repositories",
    description="Requires `repo:read` permission.",
    operation_id="list_user_repos",
    tags=["user", "internal"],
    response_model=UserRepoListResponse,
)
async def list_user_repos(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireUser())],
    params: Annotated[UserRepoListParams, Query()],
):
    repos, page_info = await service.get_user_repos(
        session,
        user=authorized.user,
        user_can_read=params.has_read_permission,
        user_can_write=params.has_write_permission,
        page=params.page,
        page_size=params.page_size,
    )

    repo_list = UserRepoListResponse.build(repos, page_info)
    for repo_read, repo in zip(repo_list.items, repos):
        repo_read.permissions = UserRepoPermissions(
            read=(
                repo.status in (RepoStatus.ENABLED, RepoStatus.READONLY)
                and authorized.comply(
                    can_read_logs_from_repo(repo_read.id, on_all_entities=True)
                )
            ),
            write=(
                repo.status == RepoStatus.ENABLED
                and authorized.comply(can_write_logs_to_repo(repo_read.id))
            ),
            readable_entities=list(
                authorized.permissions.get_repo_readable_entities(repo_read.id)
            ),
        )

    return repo_list


@router.delete(
    "/repos/{repo_id}",
    summary="Delete log repository",
    description="Requires `repo:write` permission.",
    operation_id="delete_repo",
    tags=["repo"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def delete_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_write_repo()))],
    repo_id: UUID,
):
    await service.delete_repo(session, repo_id)
