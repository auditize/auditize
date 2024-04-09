from typing import Annotated
from datetime import datetime

from pydantic import BaseModel, Field, BeforeValidator, field_serializer

from auditize.repos.models import Repo, RepoUpdate
from auditize.common.utils import serialize_datetime
from auditize.common.pagination.page.api_models import PagePaginatedResponse

class RepoCreationRequest(BaseModel):
    name: str = Field(description="The repository name")

    def to_repo(self):
        return Repo.model_validate(self.model_dump())


class RepoUpdateRequest(BaseModel):
    name: str = Field(description="The repository name")

    def to_repo_update(self):
        return RepoUpdate.model_validate(self.model_dump())


class RepoCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The repository ID")


class RepoReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The repository ID")
    name: str = Field(description="The repository name")
    created_at: datetime = Field(description="The creation date")

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value)

    @classmethod
    def from_repo(cls, repo: Repo):
        return cls.model_validate(repo.model_dump())


class RepoListResponse(PagePaginatedResponse[Repo, RepoReadingResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> RepoReadingResponse:
        return RepoReadingResponse.from_repo(repo)
