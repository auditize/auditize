from datetime import datetime
from enum import StrEnum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from auditize.api.models.common import IdField
from auditize.api.models.dates import (
    CreatedAtField,
    HasDatetimeSerialization,
    UpdatedAtField,
)
from auditize.api.models.page_pagination import (
    PagePaginatedResponse,
    PagePaginationParams,
)
from auditize.api.models.search import PagePaginatedSearchParams
from auditize.repo.sql_models import Repo, RepoStatus


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


class RepoCreate(BaseModel):
    name: str = _RepoNameField()
    status: RepoStatus = _RepoStatusField(default=RepoStatus.ENABLED)
    retention_period: Optional[int] = _RepoRetentionPeriodField(default=None)
    log_i18n_profile_id: Optional[UUID] = _RepoLogI18nProfileIdField(default=None)


class RepoUpdate(BaseModel):
    name: str = _RepoNameField(default=None)
    status: RepoStatus = _RepoStatusField(default=None)
    retention_period: Optional[int] = _RepoRetentionPeriodField(default=None)
    log_i18n_profile_id: Optional[UUID] = _RepoLogI18nProfileIdField(default=None)


class RepoStats(BaseModel, HasDatetimeSerialization):
    last_log_date: datetime | None = Field(description="The last log date")
    log_count: int = Field(description="The log count")
    storage_size: int = Field(description="The database storage size")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "last_log_date": "2024-01-03T00:00:00.000Z",
                "log_count": 1000,
                "storage_size": 100889890,
            }
        }
    )


class _BaseRepoResponse(BaseModel):
    id: UUID = _RepoIdField()
    name: str = _RepoNameField()


class RepoResponse(_BaseRepoResponse, HasDatetimeSerialization):
    created_at: datetime = CreatedAtField()
    updated_at: datetime = UpdatedAtField()
    status: RepoStatus = _RepoStatusField()
    retention_period: int | None = _RepoRetentionPeriodField()
    log_i18n_profile_id: UUID | None = _RepoLogI18nProfileIdField()


class RepoWithStatsResponse(RepoResponse):
    stats: RepoStats | None = Field(
        description="The repository stats (available if `include=stats` has been set in query parameters)"
    )

    @classmethod
    def from_repo(cls, repo: Repo):
        return cls(
            id=repo.id,
            name=repo.name,
            created_at=repo.created_at,
            updated_at=repo.updated_at,
            status=repo.status,
            retention_period=repo.retention_period,
            log_i18n_profile_id=repo.log_i18n_profile_id,
            stats=None,
        )


class RepoIncludeOptions(StrEnum):
    STATS = "stats"


class RepoListParams(PagePaginatedSearchParams):
    include: list[RepoIncludeOptions] = Field(
        default_factory=list, description="The extra fields to include in the response"
    )


class RepoListResponse(PagePaginatedResponse[Repo, RepoWithStatsResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> RepoWithStatsResponse:
        return RepoWithStatsResponse.from_repo(repo)


class UserRepoPermissions(BaseModel):
    read: bool = Field(
        description="Whether authenticated can read logs on the repository"
    )
    write: bool = Field(
        description="Whether authenticated can write logs into the repository"
    )
    readable_entities: list[str] = Field(
        description="The entities the authenticated can access on read. Empty list means all entities.",
    )


class UserRepoResponse(_BaseRepoResponse):
    permissions: UserRepoPermissions = Field(description="The repository permissions")


class UserRepoListParams(PagePaginationParams):
    has_read_permission: bool = Field(
        description="Set to true to filter repositories on which user can read logs",
        default=False,
    )
    has_write_permission: bool = Field(
        description="Set to true to filter repositories on which user can write logs",
        default=False,
    )


class UserRepoListResponse(PagePaginatedResponse[Repo, UserRepoResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> UserRepoResponse:
        return UserRepoResponse(
            id=repo.id,
            name=repo.name,
            permissions=UserRepoPermissions(
                read=False, write=False, readable_entities=[]
            ),
        )
