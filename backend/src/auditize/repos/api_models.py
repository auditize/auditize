from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from auditize.helpers.datetime import serialize_datetime
from auditize.helpers.pagination.page.api_models import PagePaginatedResponse
from auditize.repos.models import Repo, RepoStatus


class RepoCreationRequest(BaseModel):
    name: str = Field(description="The repository name")
    status: RepoStatus = Field(
        description="The repository status", default=RepoStatus.enabled
    )

    def to_repo(self):
        return Repo.model_validate(self.model_dump())


class RepoUpdateRequest(BaseModel):
    name: Optional[str] = Field(description="The repository name", default=None)
    status: Optional[RepoStatus] = Field(
        description="The repository status", default=None
    )


class RepoCreationResponse(BaseModel):
    id: str = Field(description="The repository ID")


class RepoStatsData(BaseModel):
    first_log_date: Optional[datetime] = Field(description="The first log date")
    last_log_date: Optional[datetime] = Field(description="The last log date")
    log_count: int = Field(description="The log count")
    storage_size: int = Field(description="The storage size")

    @field_serializer("first_log_date", "last_log_date", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value) if value else None


class RepoLogPermissionsData(BaseModel):
    read_logs: bool = Field(
        description="Whether authenticated can read logs on the repository"
    )
    write_logs: bool = Field(
        description="Whether authenticated can write logs into the repository"
    )


class _BaseRepoReadingResponse(BaseModel):
    id: str = Field(description="The repository ID")
    name: str = Field(description="The repository name")

    @classmethod
    def from_repo(cls, repo: Repo):
        return cls.model_validate(repo.model_dump())


class RepoReadingResponse(_BaseRepoReadingResponse):
    created_at: datetime = Field(description="The creation date")
    status: RepoStatus = Field(description="The repository status")
    stats: Optional[RepoStatsData] = Field(
        description="The repository stats", default=None
    )

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value)


class UserRepoReadingResponse(_BaseRepoReadingResponse):
    permissions: RepoLogPermissionsData = Field(
        description="The repository permissions",
        default_factory=lambda: RepoLogPermissionsData(
            read_logs=False, write_logs=False
        ),
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
