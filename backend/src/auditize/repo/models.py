from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

if TYPE_CHECKING:
    from auditize.log_i18n_profile.sql_models import LogI18nProfile

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.exceptions import UnknownModelException
from auditize.log_i18n_profile.service import get_log_i18n_profile
from auditize.log_i18n_profile.sql_models import LogI18nProfile
from auditize.repo.sql_models import Repo, RepoStatus
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.models import HasCreatedAt, HasId
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


class RepoCreate(BaseModel):
    name: str = _RepoNameField()
    status: RepoStatus = _RepoStatusField(default=RepoStatus.enabled)
    retention_period: Optional[int] = _RepoRetentionPeriodField(default=None)
    log_i18n_profile_id: Optional[UUID] = _RepoLogI18nProfileIdField(default=None)


class RepoUpdate(BaseModel):
    name: str = _RepoNameField(default=None)
    status: RepoStatus = _RepoStatusField(default=None)
    retention_period: Optional[int] = _RepoRetentionPeriodField(default=None)
    log_i18n_profile_id: Optional[UUID] = _RepoLogI18nProfileIdField(default=None)


class RepoStats(BaseModel, HasDatetimeSerialization):
    first_log_date: datetime | None = Field(
        default=None, description="The first log date"
    )
    last_log_date: datetime | None = Field(
        default=None, description="The last log date"
    )
    log_count: int = Field(default=0, description="The log count")
    storage_size: int = Field(default=0, description="The database storage size")

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


class _BaseRepoResponse(BaseModel):
    id: UUID = _RepoIdField()
    name: str = _RepoNameField()


class RepoResponse(_BaseRepoResponse, HasDatetimeSerialization):
    status: RepoStatus = _RepoStatusField()
    retention_period: int | None = _RepoRetentionPeriodField()
    log_i18n_profile_id: UUID | None = _RepoLogI18nProfileIdField()
    stats: RepoStats | None = Field(
        default=None,
        description="The repository stats (available if `include=stats` has been set in query parameters)",
    )
    created_at: datetime = Field(description="The repository creation date")

    @classmethod
    def from_repo(cls, repo: Repo):
        return cls.model_validate(repo, from_attributes=True)


class RepoListResponse(PagePaginatedResponse[Repo, RepoResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> RepoResponse:
        return RepoResponse.from_repo(repo)


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
    permissions: UserRepoPermissions = Field(
        description="The repository permissions",
        # NB: we have to use a default value here because the permissions field will be
        # set after the model initialization
        default_factory=lambda: UserRepoPermissions(
            read=False, write=False, readable_entities=[]
        ),
    )


class UserRepoListResponse(PagePaginatedResponse[Repo, UserRepoResponse]):
    @classmethod
    def build_item(cls, repo: Repo) -> UserRepoResponse:
        return UserRepoResponse.model_validate(repo, from_attributes=True)
