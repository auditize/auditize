from typing import Annotated

from fastapi import APIRouter, Depends, Query

from auditize.repos.api_models import RepoCreationRequest, RepoCreationResponse, RepoReadingResponse, \
    RepoListResponse, RepoUpdateRequest, RepoIncludeOptions, RepoStatsData
from auditize.repos import service
from auditize.common.mongo import DatabaseManager, get_dbm

router = APIRouter()


@router.post(
    "/repos",
    summary="Create log repository",
    tags=["repos"],
    status_code=201
)
async def create_repo(
        dbm: Annotated[DatabaseManager, Depends(get_dbm)], repo: RepoCreationRequest
) -> RepoCreationResponse:
    repo_id = await service.create_repo(dbm, repo.to_repo())
    return RepoCreationResponse(id=repo_id)


@router.patch(
    "/repos/{repo_id}",
    summary="Update log repository",
    tags=["repos"],
    status_code=204
)
async def update_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    repo_id: str, repo: RepoUpdateRequest
):
    await service.update_repo(dbm, repo_id, repo.to_repo_update())
    return None


@router.get(
    "/repos/{repo_id}",
    summary="Get log repository",
    tags=["repos"],
    response_model=RepoReadingResponse
)
async def get_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    repo_id: str,
    include: Annotated[list[RepoIncludeOptions], Query()] = ()
) -> RepoReadingResponse:
    repo = await service.get_repo(dbm, repo_id)
    response = RepoReadingResponse.from_repo(repo)
    if RepoIncludeOptions.STATS in include:
        stats = await service.get_repo_stats(dbm, repo.id)
        response.stats = RepoStatsData.model_validate(stats.model_dump())
    return response


@router.get(
    "/repos",
    summary="List log repositories",
    tags=["repos"],
    response_model=RepoListResponse
)
async def list_repos(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    include: Annotated[list[RepoIncludeOptions], Query()] = (),
    page: int = 1, page_size: int = 10
) -> RepoListResponse:
    repos, page_info = await service.get_repos(dbm, page, page_size)
    response = RepoListResponse.build(repos, page_info)
    if RepoIncludeOptions.STATS in include:
        for repo in response.data:
            stats = await service.get_repo_stats(dbm, repo.id)
            repo.stats = RepoStatsData.model_validate(stats.model_dump())
    return response


@router.delete(
    "/repos/{repo_id}",
    summary="Delete log repository",
    tags=["repos"],
    status_code=204
)
async def delete_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], repo_id: str
):
    await service.delete_repo(dbm, repo_id)
