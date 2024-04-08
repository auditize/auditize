from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.repos.api_models import RepoCreationRequest, RepoCreationResponse
from auditize.repos.models import Repo
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
    repo_id = await service.create_repo(db, Repo(name=repo.name))
    return RepoCreationResponse(id=repo_id)
