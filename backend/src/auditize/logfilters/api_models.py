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


def _ColumnsField():  # noqa
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
    )


class LogFilterCreationRequest(BaseModel):
    name: str = Field(...)
    repo_id: str = Field(...)
    search_params: LogFilterSearchParamsData = Field(...)
    columns: list[str] = _ColumnsField()

    @field_validator("columns")
    def validate_columns(cls, columns: list[str]) -> list[str]:
        for column in columns:
            if (
                not column in _BUILTIN_FILTER_COLUMNS
                and not FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN.match(column)
            ):
                raise ValueError(f"Invalid column name: {column}")
        return columns


class LogFilterCreationResponse(BaseModel):
    id: str
