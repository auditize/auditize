from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from auditize.helpers.api.validators import FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN
from auditize.logs.api_models import BaseLogSearchParams

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
    "attachment_description",
    "node",
)
_CUSTOM_FIELD_GROUPS = (
    "actor",
    "resource",
    "source",
    "details",
)


class LogFilterSearchParamsData(BaseLogSearchParams):
    model_config = ConfigDict(extra="allow")

    @model_validator(mode="after")
    def validate_extra(self):
        for name in self.__pydantic_extra__:
            if not FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN.match(name):
                raise ValueError(f"Invalid custom field name: {name}")
        return self


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


class _ValidateColumnsMixin:
    @field_validator("columns")
    def validate_columns(cls, columns: list[str]) -> list[str]:
        for column in columns:
            if (
                not column in _BUILTIN_FILTER_COLUMNS
                and not FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN.match(column)
            ):
                raise ValueError(f"Invalid column name: {column}")
        return columns


class LogFilterCreationRequest(BaseModel, _ValidateColumnsMixin):
    name: str = _NameField()
    repo_id: str = _RepoIdField()
    search_params: LogFilterSearchParamsData = _SearchParamsField()
    columns: list[str] = _ColumnsField()


class LogFilterCreationResponse(BaseModel):
    id: str


class LogFilterUpdateRequest(BaseModel, _ValidateColumnsMixin):
    name: Optional[str] = _NameField(default=None)
    repo_id: Optional[str] = _RepoIdField(default=None)
    search_params: Optional[LogFilterSearchParamsData] = _SearchParamsField(
        default=None
    )
    columns: Optional[list[str]] = _ColumnsField(default=None)
