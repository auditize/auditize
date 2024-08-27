import csv
from functools import partial
from io import StringIO
from itertools import count
from typing import Any, AsyncGenerator
from uuid import UUID

from auditize.config import get_config
from auditize.exceptions import (
    ValidationError,
)
from auditize.helpers.datetime import serialize_datetime
from auditize.i18n import Lang, t
from auditize.log.db import get_log_db_for_reading
from auditize.log.models import CustomField, Log, LogSearchParams
from auditize.log.service.main import get_logs
from auditize.log_i18n_profile.models import LogI18nProfile, get_log_value_translation
from auditize.repo.service import get_repo

CSV_BUILTIN_COLUMNS = (
    "log_id",
    "saved_at",
    "action_type",
    "action_category",
    "actor_ref",
    "actor_type",
    "actor_name",
    "resource_ref",
    "resource_type",
    "resource_name",
    "tag_ref",
    "tag_type",
    "tag_name",
    "attachment_name",
    "attachment_type",
    "attachment_mime_type",
    "entity_path:ref",
    "entity_path:name",
)


def _custom_fields_to_dict(custom_fields: list[CustomField], prefix: str) -> dict:
    return {f"{prefix}.{field.name}": field.value for field in custom_fields}


def _log_to_dict(
    log: Log, log_i18n_profile: LogI18nProfile | None, lang: Lang
) -> dict[str, Any]:
    translator = partial(get_log_value_translation, log_i18n_profile, lang)
    data = dict()
    data["log_id"] = str(log.id)
    data["action_category"] = translator("action_category", log.action.category)
    data["action_type"] = translator("action_type", log.action.type)
    data.update(_custom_fields_to_dict(log.source, "source"))
    if log.actor:
        data["actor_type"] = translator("actor_type", log.actor.type)
        data["actor_name"] = log.actor.name
        data["actor_ref"] = log.actor.ref
        data.update(_custom_fields_to_dict(log.actor.extra, "actor"))
    if log.resource:
        data["resource_type"] = translator("resource_type", log.resource.type)
        data["resource_name"] = log.resource.name
        data["resource_ref"] = log.resource.ref
        data.update(_custom_fields_to_dict(log.resource.extra, "resource"))
    data.update(_custom_fields_to_dict(log.details, "details"))
    data["tag_ref"] = "|".join(tag.ref or "" for tag in log.tags)
    data["tag_type"] = "|".join(translator("tag_type", tag.type) for tag in log.tags)
    data["tag_name"] = "|".join(tag.name or "" for tag in log.tags)
    data["attachment_name"] = "|".join(
        attachment.name for attachment in log.attachments
    )
    data["attachment_type"] = "|".join(
        translator("attachment_type", attachment.type) for attachment in log.attachments
    )
    data["attachment_mime_type"] = "|".join(
        attachment.mime_type for attachment in log.attachments
    )
    data["entity_path:ref"] = " > ".join(entity.ref for entity in log.entity_path)
    data["entity_path:name"] = " > ".join(entity.name for entity in log.entity_path)
    data["saved_at"] = serialize_datetime(log.saved_at)

    return data


def _log_dict_to_csv_row(log: dict[str, Any], columns: list[str]) -> list[str]:
    return [log.get(col, "") for col in columns]


def _translate_csv_column(
    col: str, log_i18n_profile: LogI18nProfile | None, lang: Lang
) -> str:
    normalized_col = _parse_csv_column(col)

    if len(normalized_col) == 1:  # builtin log field
        return t("log.csv.column." + normalized_col[0], lang=lang)

    # otherwise, it's a custom field

    return "%s: %s" % (
        t("log.csv.column." + normalized_col[0], lang=lang),
        get_log_value_translation(
            log_i18n_profile, lang, normalized_col[0], normalized_col[1]
        ),
    )


def _parse_csv_column(col: str) -> tuple[str, ...]:
    if col in CSV_BUILTIN_COLUMNS:
        return (col,)

    parts = col.split(".")
    if len(parts) == 2 and parts[0] in ("source", "actor", "resource", "details"):
        return tuple(parts)

    raise ValidationError(f"Invalid column name: {col!r}")


def validate_csv_columns(cols: list[str]):
    if len(cols) != len(set(cols)):
        raise ValidationError("Duplicated column names are forbidden")

    for col in cols:
        _parse_csv_column(col)


async def get_logs_as_csv(
    repo_id: UUID,
    *,
    authorized_entities: set[str] = None,
    search_params: LogSearchParams = None,
    columns: list[str],
    lang: Lang,
) -> AsyncGenerator[str, None]:
    max_rows = get_config().csv_max_rows
    returned_rows = 0
    repo = await get_repo(repo_id)
    log_i18n_profile = await repo.get_log_i18n_profile()
    logs_db = await get_log_db_for_reading(repo)
    cursor = None
    for i in count(0):
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        if i == 0:
            csv_writer.writerow(
                _translate_csv_column(col, log_i18n_profile, lang) for col in columns
            )
        logs, cursor = await get_logs(
            logs_db,
            authorized_entities=authorized_entities,
            search_params=search_params,
            pagination_cursor=cursor,
            limit=min(100, max_rows - returned_rows) if max_rows > 0 else 100,
        )
        returned_rows += len(logs)
        csv_writer.writerows(
            _log_dict_to_csv_row(_log_to_dict(log, log_i18n_profile, lang), columns)
            for log in logs
        )
        yield csv_buffer.getvalue()
        if not cursor or (max_rows > 0 and returned_rows >= max_rows):
            break
