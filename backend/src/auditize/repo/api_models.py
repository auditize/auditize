from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from auditize.repo.models import Repo, RepoStatus
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse


def _RepoLogI18nProfileIdField(**kwargs):  # noqa
    return IdField(
        description="Log i18n profile ID",
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
    return IdField(description="Repository ID")


def _RepoRetentionPeriodField(**kwargs):  # noqa
    return Field(
        description="The repository retention period in days",
        ge=1,
        json_schema_extra={"example": 30},
        **kwargs,
    )


class RepoCreationRequest(BaseModel):
    name: str = _RepoNameField()
    status: RepoStatus = _RepoStatusField(default=RepoStatus.enabled)
    retention_period: Optional[int] = _RepoRetentionPeriodField(default=None)
    log_i18n_profile_id: Optional[UUID] = _RepoLogI18nProfileIdField(default=None)


class RepoUpdateRequest(BaseModel):
    name: str = _RepoNameField(default=None)
    status: RepoStatus = _RepoStatusField(default=None)
    retention_period: Optional[int] = _RepoRetentionPeriodField(default=None)
    log_i18n_profile_id: Optional[UUID] = _RepoLogI18nProfileIdField(default=None)


class RepoCreationResponse(BaseModel):
    id: UUID = _RepoIdField()


class RepoStatsData(BaseModel, HasDatetimeSerialization):
    first_log_date: datetime | None = Field(description="The first log date")
    last_log_date: datetime | None = Field(description="The last log date")
    log_count: int = Field(description="The log count")
    storage_size: int = Field(description="The database storage size")

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
    read: bool = Field(
        description="Whether authenticated can read logs on the repository"
    )
    write: bool = Field(
        description="Whether authenticated can write logs into the repository"
    )
    readable_entities: list[str] = Field(
        description="The entities the authenticated can access on read. Empty list means all entities.",
    )


class _BaseRepoReadingResponse(BaseModel):
    id: UUID = _RepoIdField()
    name: str = _RepoNameField()


class RepoReadingResponse(_BaseRepoReadingResponse, HasDatetimeSerialization):
    status: RepoStatus = _RepoStatusField()
    retention_period: Optional[int] = _RepoRetentionPeriodField()
    log_i18n_profile_id: Optional[UUID] = _RepoLogI18nProfileIdField()
    stats: Optional[RepoStatsData] = Field(
        description="The repository stats (available if `include=stats` has been set in query parameters)",
        default=None,
    )
    created_at: datetime = Field(description="The repository creation date")


class UserRepoReadingResponse(_BaseRepoReadingResponse):
    permissions: RepoLogPermissionsData = Field(
        description="The repository permissions",
        # NB: we have to use a default value here because the permissions field will be
        # set after the model initialization
        default_factory=lambda: RepoLogPermissionsData(
            read=False, write=False, readable_entities=[]
        ),
    )


class RepoListResponse(PagePaginatedResponse[Repo, RepoReadingResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> RepoReadingResponse:
        return RepoReadingResponse.model_validate(repo.model_dump())


class UserRepoListResponse(PagePaginatedResponse[Repo, UserRepoReadingResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> UserRepoReadingResponse:
        return UserRepoReadingResponse.model_validate(repo.model_dump())


class RepoIncludeOptions(Enum):
    STATS = "stats"
