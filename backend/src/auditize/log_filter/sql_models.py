from uuid import UUID

from sqlalchemy import JSON, Text, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column

from auditize.database.dbm import Base
from auditize.log_filter.models import LogFilterSearchParams
from auditize.resource.sql_models import HasCreatedAt, HasId


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

    name: Mapped[str] = mapped_column(unique=True, index=True)
    repo_id: Mapped[UUID] = mapped_column()
    user_id: Mapped[UUID] = mapped_column()
    search_params: Mapped[LogFilterSearchParams] = mapped_column(
        LogFilterSearchParamsAsJSON()
    )
    columns: Mapped[list[str]] = mapped_column(LogFilterColumnsAsList())
    is_favorite: Mapped[bool] = mapped_column(default=False)  # Added in 0.3.0
