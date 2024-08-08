from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from auditize.apikey.models import ApikeyUpdate
from auditize.apikey.service import update_apikey
from auditize.auth.authorizer import (
    Authenticated,
    Authorized,
    AuthorizedOnLogsRead,
    get_authenticated,
)
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import PermissionDenied
from auditize.helpers.api.errors import error_responses
from auditize.log_i18n_profile.api_models import LogTranslation
from auditize.permissions.assertions import (
    can_read_logs,
    can_read_repos,
    can_write_logs,
    can_write_repos,
    permissions_and,
)
from auditize.permissions.models import (
    LogPermissions,
    Permissions,
    RepoLogPermissions,
)
from auditize.repo import service
from auditize.repo.api_models import (
    RepoCreationRequest,
    RepoCreationResponse,
    RepoIncludeOptions,
    RepoListResponse,
    RepoLogPermissionsData,
    RepoReadingResponse,
    RepoStatsData,
    RepoUpdateRequest,
    UserRepoListResponse,
)
from auditize.repo.models import Repo, RepoStatus, RepoUpdate
from auditize.resource.api_models import ResourceSearchParams
from auditize.resource.pagination.page.api_models import PagePaginationParams
from auditize.user.models import Lang, UserUpdate
from auditize.user.service import update_user

router = APIRouter(responses=error_responses(401, 403))


@router.post(
    "/repos",
    summary="Create log repository",
    tags=["repos"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_repos()),
    repo: RepoCreationRequest,
) -> RepoCreationResponse:
    repo_id = await service.create_repo(dbm, Repo.model_validate(repo.model_dump()))

    # Ensure that authenticated will have read & write logs permissions on the repo he created
    if not authenticated.comply(permissions_and(can_read_logs(), can_write_logs())):
        grant_rw_on_repo_logs = Permissions(
            logs=LogPermissions(
                repos=[RepoLogPermissions(repo_id=repo_id, read=True, write=True)]
            ),
        )
        if authenticated.apikey:
            await update_apikey(
                dbm,
                authenticated.apikey.id,
                ApikeyUpdate(permissions=grant_rw_on_repo_logs),
            )
        if authenticated.user:
            await update_user(
                dbm,
                authenticated.user.id,
                UserUpdate(permissions=grant_rw_on_repo_logs),
            )
    return RepoCreationResponse(id=repo_id)


@router.patch(
    "/repos/{repo_id}",
    summary="Update log repository",
    tags=["repos"],
    status_code=204,
    responses=error_responses(400, 404, 409),
)
async def update_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_repos()),
    repo_id: UUID,
    update: RepoUpdateRequest,
):
    await service.update_repo(
        dbm, repo_id, RepoUpdate.model_validate(update.model_dump(exclude_unset=True))
    )
    return None


async def _handle_repo_include_options(
    repo_response: RepoReadingResponse,
    include: list[RepoIncludeOptions],
    dbm: DatabaseManager,
):
    if RepoIncludeOptions.STATS in include:
        stats = await service.get_repo_stats(dbm, repo_response.id)
        repo_response.stats = RepoStatsData.model_validate(stats.model_dump())


@router.get(
    "/repos/{repo_id}",
    summary="Get log repository",
    tags=["repos"],
    responses=error_responses(404),
)
async def get_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_repos()),
    repo_id: UUID,
    include: Annotated[list[RepoIncludeOptions], Query()] = (),
) -> RepoReadingResponse:
    repo = await service.get_repo(dbm, repo_id)
    response = RepoReadingResponse.model_validate(repo.model_dump())
    await _handle_repo_include_options(response, include, dbm)
    return response


@router.get(
    "/repos/{repo_id}/translation",
    summary="Get log repository translation for the authenticated user",
    tags=["repos"],
    responses=error_responses(404),
)
async def get_repo_translation_for_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: UUID,
) -> LogTranslation:
    authenticated.ensure_user()
    translation = await service.get_repo_translation(
        dbm, repo_id, authenticated.user.lang
    )
    return LogTranslation.model_validate(translation.model_dump())


@router.get(
    "/repos/{repo_id}/translations/{lang}",
    summary="Get log repository translation",
    tags=["repos"],
    responses=error_responses(404),
)
async def get_repo_translation(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: UUID,
    lang: Lang,
) -> LogTranslation:
    translation = await service.get_repo_translation(dbm, repo_id, lang)
    return LogTranslation.model_validate(translation.model_dump())


@router.get(
    "/repos",
    summary="List log repositories",
    tags=["repos"],
)
async def list_repos(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_repos()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    include: Annotated[list[RepoIncludeOptions], Query(default_factory=list)],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> RepoListResponse:
    repos, page_info = await service.get_repos(
        dbm,
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    response = RepoListResponse.build(repos, page_info)
    if include:
        for repo in response.items:
            await _handle_repo_include_options(repo, include, dbm)
    return response


@router.get(
    "/users/me/repos",
    summary="List user accessible repositories",
    tags=["users"],
)
async def list_user_repos(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    has_read_permission: Annotated[
        bool,
        Query(
            description="Set to true to filter repositories on which user can read logs",
        ),
    ] = False,
    has_write_permission: Annotated[
        bool,
        Query(
            description="Set to true to filter repositories on which user can write logs",
        ),
    ] = False,
    page_params: Annotated[PagePaginationParams, Depends()] = PagePaginationParams(),
) -> UserRepoListResponse:
    if not authenticated.user:
        raise PermissionDenied("This endpoint is only available for users")

    repos, page_info = await service.get_user_repos(
        dbm,
        user=authenticated.user,
        user_can_read=has_read_permission,
        user_can_write=has_write_permission,
        page=page_params.page,
        page_size=page_params.page_size,
    )

    response = UserRepoListResponse.build(repos, page_info)
    for repo_response, repo in zip(response.items, repos):
        repo_response.permissions = RepoLogPermissionsData(
            read=(
                repo.status in (RepoStatus.enabled, RepoStatus.readonly)
                and authenticated.comply(can_read_logs(repo_response.id))
            ),
            write=(
                repo.status == RepoStatus.enabled
                and authenticated.comply(can_write_logs(repo_response.id))
            ),
            readable_nodes=authenticated.permissions.logs.get_repo_readable_nodes(
                repo_response.id
            ),
        )

    return response


@router.delete(
    "/repos/{repo_id}",
    summary="Delete log repository",
    tags=["repos"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_repos()),
    repo_id: UUID,
):
    await service.delete_repo(dbm, repo_id)
