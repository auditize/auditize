from typing import Annotated

from fastapi import APIRouter, Depends, Query

from auditize.repos.api_models import RepoCreationRequest, RepoCreationResponse, RepoReadingResponse, \
    RepoListResponse, RepoUpdateRequest, RepoIncludeOptions, RepoStatsData, RepoLogPermissionsData
from auditize.repos import service
from auditize.common.db import DatabaseManager, get_dbm
from auditize.auth import Authenticated, get_authenticated
from auditize.permissions.assertions import can_read_logs, can_write_logs, permissions_or, permissions_and
from auditize.integrations.service import update_integration
from auditize.integrations.models import IntegrationUpdate
from auditize.users.service import update_user
from auditize.users.models import UserUpdate
from auditize.permissions.models import Permissions, LogsPermissions, ReadWritePermissions

router = APIRouter()


@router.post(
    "/repos",
    summary="Create log repository",
    tags=["repos"],
    status_code=201
)
async def create_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo: RepoCreationRequest
) -> RepoCreationResponse:
    repo_id = await service.create_repo(dbm, repo.to_repo())

    # Ensure that authenticated will have read & write logs permissions on the repo he created
    if not authenticated.comply(permissions_and(can_read_logs(), can_write_logs())):
        grant_rw_on_repo_logs = Permissions(
            logs=LogsPermissions(repos={str(repo_id): ReadWritePermissions.yes()})
        )
        if authenticated.integration:
            await update_integration(
                dbm, authenticated.integration.id,
                IntegrationUpdate(permissions=grant_rw_on_repo_logs)
            )
        if authenticated.user:
            await update_user(
                dbm, authenticated.user.id,
                UserUpdate(permissions=grant_rw_on_repo_logs)
            )
    return RepoCreationResponse(id=repo_id)


@router.patch(
    "/repos/{repo_id}",
    summary="Update log repository",
    tags=["repos"],
    status_code=204
)
async def update_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str, repo: RepoUpdateRequest
):
    await service.update_repo(dbm, repo_id, repo.to_repo_update())
    return None


async def _handle_repo_include_options(
    repo_response: RepoReadingResponse, include: list[RepoIncludeOptions],
    dbm: DatabaseManager, authenticated: Authenticated
):
    if RepoIncludeOptions.STATS in include:
        stats = await service.get_repo_stats(dbm, repo_response.id)
        repo_response.stats = RepoStatsData.model_validate(stats.model_dump())
    if RepoIncludeOptions.PERMISSIONS in include:
        repo_response.permissions = RepoLogPermissionsData(
            read_logs=authenticated.comply(can_read_logs(repo_response.id)),
            write_logs=authenticated.comply(can_write_logs(repo_response.id))
        )


@router.get(
    "/repos/{repo_id}",
    summary="Get log repository",
    tags=["repos"],
    response_model=RepoReadingResponse
)
async def get_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    include: Annotated[list[RepoIncludeOptions], Query()] = ()
) -> RepoReadingResponse:
    repo = await service.get_repo(dbm, repo_id)
    response = RepoReadingResponse.from_repo(repo)
    await _handle_repo_include_options(response, include, dbm, authenticated)
    return response


@router.get(
    "/repos",
    summary="List log repositories",
    tags=["repos"],
    response_model=RepoListResponse
)
async def list_repos(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    include: Annotated[list[RepoIncludeOptions], Query()] = (),
    has_log_permission: Annotated[bool, Query(description="Filter repositories on which authenticated at least a read or write permission on log")] = False,
    page: int = 1, page_size: int = 10
) -> RepoListResponse:
    repo_ids = None
    if has_log_permission and not authenticated.comply(permissions_or(can_read_logs(), can_write_logs())):
        repo_ids = authenticated.permissions.logs.repos.keys()
    repos, page_info = await service.get_repos(
        dbm, repo_ids=repo_ids, page=page, page_size=page_size
    )
    response = RepoListResponse.build(repos, page_info)
    if include:
        for repo in response.data:
            await _handle_repo_include_options(repo, include, dbm, authenticated)
    return response


@router.delete(
    "/repos/{repo_id}",
    summary="Delete log repository",
    tags=["repos"],
    status_code=204
)
async def delete_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str
):
    await service.delete_repo(dbm, repo_id)
