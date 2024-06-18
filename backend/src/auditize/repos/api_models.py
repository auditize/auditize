from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from auditize.helpers.datetime import serialize_datetime
from auditize.helpers.pagination.page.api_models import PagePaginatedResponse
from auditize.repos.models import Repo, RepoStatus


def _RepoLogI18nProfileIdField(**kwargs):  # noqa
    return Field(
        description="The log i18n profile ID",
        json_schema_extra={
            "example": "FEC4A4E6-AC13-455F-A0F8-E71AA0C37B7D",
        },
        **kwargs,
    )


def _RepoNameField(**kwargs):  # noqa
    return Field(
        description="The repository name",
        json_schema_extra={
            "example": "My repository",
        },
        **kwargs,
    )


def _RepoStatusField(**kwargs):  # noqa
    return Field(
        description="The repository status",
        json_schema_extra={
            "example": "enabled",
        },
        **kwargs,
    )


def _RepoIdField():  # noqa
    return Field(
        description="The repository ID",
        json_schema_extra={"example": "FEC4A4E6-AC13-455F-A0F8-E71AA0C37B7D"},
    )


class RepoCreationRequest(BaseModel):
    name: str = _RepoNameField()
    status: RepoStatus = _RepoStatusField(default=RepoStatus.enabled)
    log_i18n_profile_id: Optional[str] = _RepoLogI18nProfileIdField(default=None)

    def to_repo(self):
        return Repo.model_validate(self.model_dump())


class RepoUpdateRequest(BaseModel):
    name: Optional[str] = _RepoNameField(default=None)
    status: Optional[RepoStatus] = _RepoStatusField(default=None)
    log_i18n_profile_id: Optional[str] = _RepoLogI18nProfileIdField(default=None)


class RepoCreationResponse(BaseModel):
    id: str = _RepoIdField()


class RepoStatsData(BaseModel):
    first_log_date: datetime | None = Field(description="The first log date")
    last_log_date: datetime | None = Field(description="The last log date")
    log_count: int = Field(description="The log count")
    storage_size: int = Field(description="The database storage size")

    @field_serializer("first_log_date", "last_log_date", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value) if value else None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_log_date": "2024-01-01T00:00:00Z",
                "last_log_date": "2024-01-03T00:00:00Z",
                "log_count": 1000,
                "storage_size": 100889890,
            }
        }
    )


class RepoLogPermissionsData(BaseModel):
    read_logs: bool = Field(
        description="Whether authenticated can read logs on the repository"
    )
    write_logs: bool = Field(
        description="Whether authenticated can write logs into the repository"
    )
    nodes: list[str] = Field(
        description="The nodes the authenticated can access on read. Empty list means all nodes.",
    )


class _BaseRepoReadingResponse(BaseModel):
    id: str = _RepoIdField()
    name: str = _RepoNameField()

    @classmethod
    def from_repo(cls, repo: Repo):
        return cls.model_validate(repo.model_dump())


class RepoReadingResponse(_BaseRepoReadingResponse):
    status: RepoStatus = _RepoStatusField()
    log_i18n_profile_id: Optional[str] = _RepoLogI18nProfileIdField()
    stats: Optional[RepoStatsData] = Field(
        description="The repository stats (available if `include=stats` has been set in query parameters)",
        default=None,
    )
    created_at: datetime = Field(description="The repository creation date")

    @field_serializer("created_at", when_used="json")
    def serialize_datetime(self, value):
        return serialize_datetime(value)


class UserRepoReadingResponse(_BaseRepoReadingResponse):
    permissions: RepoLogPermissionsData = Field(
        description="The repository permissions",
        # NB: we have to use a default value here because the permissions field will be
        # set after the model initialization
        default_factory=lambda: RepoLogPermissionsData(
            read_logs=False, write_logs=False, nodes=[]
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
