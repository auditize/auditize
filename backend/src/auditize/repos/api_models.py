from enum import Enum
from typing import Annotated, Optional
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


class RepoStatsData(BaseModel):
    first_log_date: Optional[datetime] = Field(description="The first log date")
    last_log_date: Optional[datetime] = Field(description="The last log date")
    log_count: int = Field(description="The log count")
    storage_size: int = Field(description="The storage size")


class RepoLogPermissionsData(BaseModel):
    read_logs: bool = Field(description="Whether authenticated can read logs on the repository")
    write_logs: bool = Field(description="Whether authenticated can write logs into the repository")


class RepoReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The repository ID")
    name: str = Field(description="The repository name")
    created_at: datetime = Field(description="The creation date")
    stats: Optional[RepoStatsData] = Field(description="The repository stats", default=None)

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value)

    @classmethod
    def from_repo(cls, repo: Repo):
        return cls.model_validate(repo.model_dump())


class UserRepoReadingResponse(RepoReadingResponse):
    permissions: RepoLogPermissionsData = Field(
        description="The repository permissions",
        default_factory=lambda: RepoLogPermissionsData(read_logs=False, write_logs=False)
    )


class RepoListResponse(PagePaginatedResponse[Repo, RepoReadingResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> RepoReadingResponse:
        return RepoReadingResponse.from_repo(repo)


class UserRepoListResponse(PagePaginatedResponse[Repo, UserRepoReadingResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> UserRepoReadingResponse:
        return UserRepoReadingResponse.from_repo(repo)


class RepoIncludeOptions(Enum):
    STATS = "stats"
