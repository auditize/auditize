from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import JSON, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from auditize.database.dbm import Base
from auditize.helpers.api.validators import (
    FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN,
    FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN_STRING,
)
from auditize.log.models import BaseLogSearchParams
from auditize.resource.api_models import HasDatetimeSerialization, IdField
from auditize.resource.pagination.page.api_models import PagePaginatedResponse
from auditize.resource.sql_models import HasCreatedAt, HasId

_BUILTIN_FILTER_COLUMNS = (
    "saved_at",
    "action",
    "action_type",
    "action_category",
    "actor",
    "actor_ref",
    "actor_type",
    "actor_name",
    "resource",
    "resource_ref",
    "resource_type",
    "resource_name",
    "tag",
    "tag_ref",
    "tag_type",
    "tag_name",
    "attachment",
    "attachment_name",
    "attachment_type",
    "attachment_mime_type",
    "entity",
)
_CUSTOM_FIELD_GROUPS = (
    "actor",
    "resource",
    "source",
    "details",
)


class LogFilterSearchParams(BaseLogSearchParams):
    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "patternProperties": {
                FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN_STRING: {
                    "type": "string",
                    "description": "Custom fields",
                }
            },
            "additionalProperties": False,
        },
    )

    @model_validator(mode="after")
    def validate_extra(self):
        for name in self.__pydantic_extra__:
            if not FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN.match(name):
                raise ValueError(f"Invalid search parameter name: {name!r}")
        return self


class LogFilterSearchParamsAsJSON(TypeDecorator):
    impl = JSON

    def process_bind_param(self, value: LogFilterSearchParams | dict, _) -> dict:
        if isinstance(value, LogFilterSearchParams):
            return value.model_dump(mode="json")
        return value

    def process_result_value(self, value: dict, _) -> LogFilterSearchParams:
        return LogFilterSearchParams.model_validate(value)


class LogFilterColumnsAsList(TypeDecorator):
    impl = Text

    def process_bind_param(self, value: list[str], _) -> str:
        return ",".join(value)

    def process_result_value(self, value: str, _) -> list[str]:
        return value.split(",") if value else []


class LogFilter(Base, HasId, HasCreatedAt):
    __tablename__ = "log_filter"

    name: Mapped[str] = mapped_column(nullable=False, unique=True, index=True)
    repo_id: Mapped[UUID] = mapped_column(nullable=False)
    user_id: Mapped[UUID] = mapped_column(nullable=False)
    search_params: Mapped[LogFilterSearchParams] = mapped_column(
        LogFilterSearchParamsAsJSON(), nullable=False
    )
    columns: Mapped[list[str]] = mapped_column(LogFilterColumnsAsList(), nullable=False)
    is_favorite: Mapped[bool] = mapped_column(
        nullable=False, default=False
    )  # Added in 0.3.0


def _FilterIdField(**kwargs):  # noqa
    return IdField(
        description="Filter ID",
        **kwargs,
    )


def _CreatedAtField(**kwargs):  # noqa
    return Field(
        description="Creation date of the filter",
        json_schema_extra={"example": "2021-10-12T09:00:00Z"},
        **kwargs,
    )


def _NameField(**kwargs):  # noqa
    return Field(
        description="Name of the filter",
        json_schema_extra={"example": "My Filter"},
        **kwargs,
    )


def _RepoIdField(**kwargs):  # noqa
    return Field(
        description="ID of the repository",
        json_schema_extra={"example": "FEC4A4E6-AC13-455F-A0F8-E71AA0C37B7D"},
        **kwargs,
    )


def _SearchParamsField(**kwargs):  # noqa
    return Field(
        description="Search parameters",
        json_schema_extra={
            "example": {
                "action_type": "some action",
                "actor_name": "some actor",
                "resource_name": "some resource",
            },
        },
        **kwargs,
    )


def _ColumnsField(**kwargs):  # noqa
    return Field(
        description=(
            "List of configured columns. Available columns are:\n"
            + "\n".join(f"- `{col}`" for col in _BUILTIN_FILTER_COLUMNS)
            + "\n"
            + "- `source.<custom-field>`\n"
            + "- `actor.<custom-field>`\n"
            + "- `resource.<custom-field>`\n"
            + "- `details.<custom-field>`\n"
        ),
        json_schema_extra={
            "example": [
                "log_id",
                "saved_at",
                "action",
                "action_type",
                "action_category",
            ],
        },
        **kwargs,
    )


def _IsFavoriteField(**kwargs):  # noqa
    return Field(
        description="Whether the filter is marked as favorite",
        json_schema_extra={"example": True},
        **kwargs,
    )


class _ValidateColumnsMixin:
    @field_validator("columns")
    def validate_columns(cls, columns: list[str]) -> list[str]:
        for column in columns:
            if (
                not column in _BUILTIN_FILTER_COLUMNS
                and not FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN.match(column)
            ):
                raise ValueError(f"Invalid column: {column}")
        if len(columns) != len(set(columns)):
            raise ValueError("Duplicated column")
        return columns


class LogFilterCreate(BaseModel, _ValidateColumnsMixin):
    name: str = _NameField()
    repo_id: UUID = _RepoIdField()
    search_params: LogFilterSearchParams = _SearchParamsField()
    columns: list[str] = _ColumnsField()
    is_favorite: bool = _IsFavoriteField(default=False)


class LogFilterUpdate(BaseModel, _ValidateColumnsMixin):
    name: str = _NameField(default=None)
    repo_id: UUID = _RepoIdField(default=None)
    search_params: LogFilterSearchParams = _SearchParamsField(default=None)
    columns: list[str] = _ColumnsField(default=None)
    is_favorite: bool = _IsFavoriteField(default=None)


class LogFilterResponse(BaseModel, HasDatetimeSerialization):
    id: UUID = _FilterIdField()
    created_at: datetime = _CreatedAtField()
    name: str = _NameField()
    repo_id: UUID = _RepoIdField()
    search_params: LogFilterSearchParams = _SearchParamsField()
    columns: list[str] = _ColumnsField()
    is_favorite: bool = _IsFavoriteField()


class LogFilterListResponse(PagePaginatedResponse[LogFilter, LogFilterResponse]):
    @classmethod
    def build_item(cls, log_filter: LogFilter) -> LogFilterResponse:
        return LogFilterResponse.model_validate(log_filter, from_attributes=True)
