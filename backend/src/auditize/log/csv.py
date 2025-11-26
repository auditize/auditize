import csv
from functools import partial
from io import StringIO
from itertools import count
from typing import Any, AsyncGenerator, Callable

from auditize.config import get_config
from auditize.exceptions import ValidationError
from auditize.helpers.datetime import serialize_datetime
from auditize.i18n import Lang, t
from auditize.log.models import (
    LOG_CSV_BUILTIN_COLUMNS,
    CustomField,
    CustomFieldType,
    Log,
    LogSearchParams,
)
from auditize.log.service import LogService
from auditize.log_i18n_profile.service import translate
from auditize.log_i18n_profile.sql_models import LogI18nProfile


def _custom_field_value_to_csv_value(
    prefix: str,
    field: CustomField,
    translator: Callable[[str, str, str], str],
    lang: Lang,
) -> str:
    match field.type:
        case CustomFieldType.ENUM:
            return translator(prefix, field.name, field.value)
        case CustomFieldType.BOOLEAN:
            return (
                t("log.csv.true", lang=lang)
                if field.value
                else t("log.csv.false", lang=lang)
            )
        case _:
            return field.value


def _custom_fields_to_dict(
    prefix: str,
    custom_fields: list[CustomField],
    translator: Callable[[str, str, str], str],
    lang: Lang,
) -> dict:
    return {
        f"{prefix}.{field.name}": (
            _custom_field_value_to_csv_value(prefix, field, translator, lang)
        )
        for field in custom_fields
    }


def _log_to_dict(
    log: Log, log_i18n_profile: LogI18nProfile | None, lang: Lang
) -> dict[str, Any]:
    translator = partial(translate, log_i18n_profile, lang)
    data = dict()
    data["log_id"] = str(log.id)
    data["action_category"] = translator("action_category", log.action.category)
    data["action_type"] = translator("action_type", log.action.type)
    data.update(_custom_fields_to_dict("source", log.source, translator, lang))
    if log.actor:
        data["actor_type"] = translator("actor_type", log.actor.type)
        data["actor_name"] = log.actor.name
        data["actor_ref"] = log.actor.ref
        data.update(_custom_fields_to_dict("actor", log.actor.extra, translator, lang))
    if log.resource:
        data["resource_type"] = translator("resource_type", log.resource.type)
        data["resource_name"] = log.resource.name
        data["resource_ref"] = log.resource.ref
        data.update(
            _custom_fields_to_dict("resource", log.resource.extra, translator, lang)
        )
    data.update(_custom_fields_to_dict("details", log.details, translator, lang))
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
        translate(log_i18n_profile, lang, normalized_col[0], normalized_col[1]),
    )


def _parse_csv_column(col: str) -> tuple[str, ...]:
    if col in LOG_CSV_BUILTIN_COLUMNS:
        return (col,)

    parts = col.split(".")
    if len(parts) == 2 and parts[0] in ("source", "actor", "resource", "details"):
        return tuple(parts)

    raise ValidationError(f"Invalid column name: {col!r}")


def validate_log_csv_columns(cols: list[str]):
    if len(cols) != len(set(cols)):
        raise ValidationError("Duplicated column names are forbidden")

    for col in cols:
        _parse_csv_column(col)


async def stream_logs_as_csv(
    log_service: LogService,
    *,
    authorized_entities: set[str] = None,
    search_params: LogSearchParams = None,
    columns: list[str],
    lang: Lang,
) -> AsyncGenerator[str, None]:
    max_rows = get_config().csv_max_rows
    returned_rows = 0
    cursor = None
    for i in count(0):
        csv_buffer = StringIO()
        csv_writer = csv.writer(csv_buffer)
        if i == 0:
            csv_writer.writerow(
                _translate_csv_column(col, log_service.repo.log_i18n_profile, lang)
                for col in columns
            )
        logs, cursor = await log_service.get_logs(
            authorized_entities=authorized_entities,
            search_params=search_params,
            pagination_cursor=cursor,
            limit=min(100, max_rows - returned_rows) if max_rows > 0 else 100,
        )
        returned_rows += len(logs)
        csv_writer.writerows(
            _log_dict_to_csv_row(
                _log_to_dict(log, log_service.repo.log_i18n_profile, lang), columns
            )
            for log in logs
        )
        yield csv_buffer.getvalue()
        if not cursor or (max_rows > 0 and returned_rows >= max_rows):
            break
