from uuid import UUID

from pydantic import BaseModel, ConfigDict

from auditize.log.models import BaseLogSearchParams
from auditize.resource.models import HasCreatedAt, HasId


class LogFilterSearchParams(BaseLogSearchParams):
    # Allow custom fields such as actor.custom_field.
    # The validation of the custom fields is done by the corresponding model
    # in api_models.py.
    model_config = ConfigDict(extra="allow")


class LogFilter(BaseModel, HasId, HasCreatedAt):
    name: str
    repo_id: UUID
    user_id: UUID
    search_params: LogFilterSearchParams
    columns: list[str]
    is_favorite: bool = False  # Added in 0.3.0


class LogFilterUpdate(BaseModel):
    name: str = None
    repo_id: UUID = None
    search_params: LogFilterSearchParams = None
    columns: list[str] = None
    is_favorite: bool = None
