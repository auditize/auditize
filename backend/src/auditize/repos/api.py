from typing import Annotated

from fastapi import APIRouter, Depends, Query

from auditize.apikeys.models import ApikeyUpdate
from auditize.apikeys.service import update_apikey
from auditize.auth.authorizer import Authenticated, Authorized, get_authenticated
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import PermissionDenied
from auditize.helpers.api.errors import error_responses
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
from auditize.repos import service
from auditize.repos.api_models import (
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
from auditize.repos.models import RepoUpdate
from auditize.users.models import UserUpdate
from auditize.users.service import update_user

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
    repo_id = await service.create_repo(dbm, repo.to_repo())

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
    repo_id: str,
    repo: RepoUpdateRequest,
):
    await service.update_repo(
        dbm, repo_id, RepoUpdate.model_validate(repo.model_dump())
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
    repo_id: str,
    include: Annotated[list[RepoIncludeOptions], Query()] = (),
) -> RepoReadingResponse:
    repo = await service.get_repo(dbm, repo_id)
    response = RepoReadingResponse.from_repo(repo)
    await _handle_repo_include_options(response, include, dbm)
    return response


@router.get(
    "/repos",
    summary="List log repositories",
    tags=["repos"],
)
async def list_repos(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_repos()),
    include: Annotated[list[RepoIncludeOptions], Query()] = (),
    page: int = 1,
    page_size: int = 10,
) -> RepoListResponse:
    repos, page_info = await service.get_repos(dbm, page=page, page_size=page_size)
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
        bool, Query(description="Filter repositories on which user can read logs")
    ] = False,
    has_write_permission: Annotated[
        bool, Query(description="Filter repositories on which user can write logs")
    ] = False,
    page: int = 1,
    page_size: int = 10,
) -> UserRepoListResponse:
    if not authenticated.user:
        raise PermissionDenied("This endpoint is only available for users")

    repos, page_info = await service.get_repos(
        dbm,
        user=authenticated.user,
        user_can_read=has_read_permission,
        user_can_write=has_write_permission,
        page=page,
        page_size=page_size,
    )

    response = UserRepoListResponse.build(repos, page_info)
    for repo_response in response.items:
        repo_response.permissions = RepoLogPermissionsData(
            read_logs=authenticated.comply(can_read_logs(repo_response.id)),
            write_logs=authenticated.comply(can_write_logs(repo_response.id)),
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
    repo_id: str,
):
    await service.delete_repo(dbm, repo_id)
