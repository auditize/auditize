from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.repos.api_models import RepoCreationRequest, RepoCreationResponse, RepoReadingResponse, \
    RepoListResponse, RepoUpdateRequest
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
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], repo_id: str
) -> RepoReadingResponse:
    repo = await service.get_repo(dbm, repo_id)
    return RepoReadingResponse.from_repo(repo)


@router.get(
    "/repos",
    summary="List log repositories",
    tags=["repos"],
    response_model=RepoListResponse
)
async def list_repos(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], page: int = 1, page_size: int = 10
) -> RepoListResponse:
    repos, page_info = await service.get_repos(dbm, page, page_size)
    return RepoListResponse.build(repos, page_info)


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
