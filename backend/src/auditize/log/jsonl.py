from typing import AsyncGenerator

from auditize.config import get_config
from auditize.log.models import LogResponse, LogSearchParams
from auditize.log.service import LogService


async def stream_logs_as_jsonl(
    log_service: LogService,
    *,
    authorized_entities: set[str] = None,
    search_params: LogSearchParams = None,
) -> AsyncGenerator[str, None]:
    max_rows = get_config().export_max_rows
    exported_rows = 0
    cursor = None
    while True:
        logs, cursor = await log_service.get_logs(
            authorized_entities=authorized_entities,
            search_params=search_params,
            pagination_cursor=cursor,
            limit=min(100, max_rows - exported_rows) if max_rows > 0 else 100,
        )
        yield "\n".join(
            LogResponse.model_validate(log.model_dump()).model_dump_json()
            for log in logs
        )
        exported_rows += len(logs)
        if not cursor or (max_rows > 0 and exported_rows >= max_rows):
            break
