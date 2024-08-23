from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from auditize.apikey.models import ApikeyUpdate
from auditize.apikey.service import update_apikey
from auditize.auth.authorizer import (
    Authorized,
    AuthorizedForLogRead,
    AuthorizedUser,
)
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile.api_models import LogTranslation
from auditize.permissions.assertions import (
    can_read_logs,
    can_read_repo,
    can_write_logs,
    can_write_repo,
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
from auditize.user.models import UserUpdate
from auditize.user.service import update_user

router = APIRouter(responses=error_responses(401, 403))


@router.post(
    "/repos",
    summary="Create log repository",
    description="Requires `repo:write` permission.",
    operation_id="create_repo",
    tags=["repo"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_repo(
    authorized: Authorized(can_write_repo()),
    repo: RepoCreationRequest,
) -> RepoCreationResponse:
    repo_id = await service.create_repo(Repo.model_validate(repo.model_dump()))

    # Ensure that authorized will have read & write logs permissions on the repo he created
    if not authorized.comply(permissions_and(can_read_logs(), can_write_logs())):
        grant_rw_on_repo_logs = Permissions(
            logs=LogPermissions(
                repos=[RepoLogPermissions(repo_id=repo_id, read=True, write=True)]
            ),
        )
        if authorized.apikey:
            await update_apikey(
                authorized.apikey.id,
                ApikeyUpdate(permissions=grant_rw_on_repo_logs),
            )
        if authorized.user:
            await update_user(
                authorized.user.id,
                UserUpdate(permissions=grant_rw_on_repo_logs),
            )
    return RepoCreationResponse(id=repo_id)


@router.patch(
    "/repos/{repo_id}",
    summary="Update log repository",
    description="Requires `repo:write` permission.",
    operation_id="update_repo",
    tags=["repo"],
    status_code=204,
    responses=error_responses(400, 404, 409),
)
async def update_repo(
    authorized: Authorized(can_write_repo()),
    repo_id: UUID,
    update: RepoUpdateRequest,
):
    await service.update_repo(
        repo_id, RepoUpdate.model_validate(update.model_dump(exclude_unset=True))
    )
    return None


async def _handle_repo_include_options(
    repo_response: RepoReadingResponse,
    include: list[RepoIncludeOptions],
):
    if RepoIncludeOptions.STATS in include:
        stats = await service.get_repo_stats(repo_response.id)
        repo_response.stats = RepoStatsData.model_validate(stats.model_dump())


@router.get(
    "/repos/{repo_id}",
    summary="Get log repository",
    description="Requires `repo:read` permission.",
    tags=["repo"],
    responses=error_responses(404),
)
async def get_repo(
    authorized: Authorized(can_read_repo()),
    repo_id: UUID,
    include: Annotated[list[RepoIncludeOptions], Query()] = (),
) -> RepoReadingResponse:
    repo = await service.get_repo(repo_id)
    response = RepoReadingResponse.model_validate(repo.model_dump())
    await _handle_repo_include_options(response, include)
    return response


@router.get(
    "/repos/{repo_id}/translation",
    summary="Get log repository translation for the authenticated user",
    description="Requires `log:read` permission.",
    operation_id="get_repo_translation_for_user",
    tags=["repo", "internal"],
    responses=error_responses(404),
)
async def get_repo_translation_for_user(
    authorized: AuthorizedUser(can_read_logs()),
    repo_id: UUID,
) -> LogTranslation:
    translation = await service.get_repo_translation(repo_id, authorized.user.lang)
    return LogTranslation.model_validate(translation.model_dump())


@router.get(
    "/repos/{repo_id}/translations/{lang}",
    summary="Get log repository translation",
    description="Requires `log:read` permission.",
    operation_id="get_repo_translation",
    tags=["repo"],
    responses=error_responses(404),
)
async def get_repo_translation(
    authorized: AuthorizedForLogRead(),
    repo_id: UUID,
    lang: Lang,
) -> LogTranslation:
    translation = await service.get_repo_translation(repo_id, lang)
    return LogTranslation.model_validate(translation.model_dump())


@router.get(
    "/repos",
    summary="List log repositories",
    description="Requires `repo:read` permission.",
    operation_id="list_repos",
    tags=["repo"],
)
async def list_repos(
    authorized: Authorized(can_read_repo()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    include: Annotated[list[RepoIncludeOptions], Query(default_factory=list)],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> RepoListResponse:
    repos, page_info = await service.get_repos(
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    response = RepoListResponse.build(repos, page_info)
    if include:
        for repo in response.items:
            await _handle_repo_include_options(repo, include)
    return response


@router.get(
    "/users/me/repos",
    summary="List user accessible repositories",
    description="Requires `repo:read` permission.",
    operation_id="list_user_repos",
    tags=["user", "internal"],
)
async def list_user_repos(
    authorized: AuthorizedUser(),
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
    repos, page_info = await service.get_user_repos(
        user=authorized.user,
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
                and authorized.comply(can_read_logs(repo_response.id))
            ),
            write=(
                repo.status == RepoStatus.enabled
                and authorized.comply(can_write_logs(repo_response.id))
            ),
            readable_entities=authorized.permissions.logs.get_repo_readable_entities(
                repo_response.id
            ),
        )

    return response


@router.delete(
    "/repos/{repo_id}",
    summary="Delete log repository",
    description="Requires `repo:write` permission.",
    operation_id="delete_repo",
    tags=["repo"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_repo(
    authorized: Authorized(can_write_repo()),
    repo_id: UUID,
):
    await service.delete_repo(repo_id)
