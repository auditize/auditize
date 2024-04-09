from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.repos.api_models import RepoCreationRequest, RepoCreationResponse, RepoReadingResponse, \
    RepoListResponse, RepoUpdateRequest
from auditize.repos import service
from auditize.common.mongo import Database, get_db

router = APIRouter()


@router.post(
    "/repos",
    summary="Create log repository",
    tags=["repos"],
    status_code=201
)
async def create_repo(
        db: Annotated[Database, Depends(get_db)], repo: RepoCreationRequest
) -> RepoCreationResponse:
    repo_id = await service.create_repo(db, repo.to_repo())
    return RepoCreationResponse(id=repo_id)


@router.patch(
    "/repos/{repo_id}",
    summary="Update log repository",
    tags=["repos"],
    status_code=204
)
async def update_repo(
    db: Annotated[Database, Depends(get_db)],
    repo_id: str, repo: RepoUpdateRequest
):
    await service.update_repo(db, repo_id, repo.to_repo_update())
    return None


@router.get(
    "/repos/{repo_id}",
    summary="Get log repository",
    tags=["repos"],
    response_model=RepoReadingResponse
)
async def get_repo(
    db: Annotated[Database, Depends(get_db)], repo_id: str
) -> RepoReadingResponse:
    repo = await service.get_repo(db, repo_id)
    return RepoReadingResponse.from_repo(repo)


@router.get(
    "/repos",
    summary="List log repositories",
    tags=["repos"],
    response_model=RepoListResponse
)
async def list_repos(
    db: Annotated[Database, Depends(get_db)], page: int = 1, page_size: int = 10
) -> RepoListResponse:
    repos, page_info = await service.get_repos(db, page, page_size)
    return RepoListResponse.build(repos, page_info)

