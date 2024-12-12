import uuid
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from auditize.exceptions import (
    InvalidPaginationCursor,
    UnknownModelException,
)
from auditize.helpers.datetime import now, serialize_datetime
from auditize.log.db import (
    LogDatabase,
    get_log_db_for_maintenance,
    get_log_db_for_reading,
    get_log_db_for_writing,
)
from auditize.log.models import Log, LogSearchParams
from auditize.log.service.consolidation import (
    check_log,
    consolidate_log,
    consolidate_log_attachment,
    purge_orphan_consolidated_log_data,
)
from auditize.repo.models import Repo
from auditize.repo.service import get_repo, get_retention_period_enabled_repos
from auditize.resource.pagination.cursor.serialization import (
    load_pagination_cursor,
    serialize_pagination_cursor,
)
from auditize.resource.service import (
    create_resource_document,
    get_resource_document,
    update_resource_document,
)

# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}


async def save_log(repo_id: UUID, log: Log) -> UUID:
    db = await get_log_db_for_writing(repo_id)

    await check_log(db, log)

    # NB: do not use transaction here to avoid possible WriteConflict errors
    # on consolidated data documents
    log_id = await create_resource_document(db.logs, log)
    await consolidate_log(db, log)

    return log_id


async def save_log_attachment(repo_id: UUID, log_id: UUID, attachment: Log.Attachment):
    db = await get_log_db_for_writing(repo_id)

    # NB: do not use transaction here to avoid possible WriteConflict errors
    # on consolidated data documents
    await update_resource_document(
        db.logs,
        log_id,
        {"attachments": attachment.model_dump()},
        operator="$push",
    )
    await consolidate_log_attachment(db, attachment)


def _log_filter(log_id: UUID, authorized_entities: set[str]):
    filter = {"_id": log_id}
    if authorized_entities:
        filter["entity_path.ref"] = {"$in": list(authorized_entities)}
    return filter


async def get_log(repo_id: UUID, log_id: UUID, authorized_entities: set[str]) -> Log:
    db = await get_log_db_for_reading(repo_id)
    document = await get_resource_document(
        db.logs,
        filter=_log_filter(log_id, authorized_entities),
        projection=_EXCLUDE_ATTACHMENT_DATA,
    )
    return Log.model_validate(document)


async def get_log_attachment(
    repo_id: UUID, log_id: UUID, attachment_idx: int, authorized_entities: set[str]
) -> Log.Attachment:
    db = await get_log_db_for_reading(repo_id)
    doc = await get_resource_document(
        db.logs,
        filter=_log_filter(log_id, authorized_entities),
        projection={"attachments": {"$slice": [attachment_idx, 1]}},
    )
    if len(doc["attachments"]) == 0:
        raise UnknownModelException()
    return Log.Attachment.model_validate(doc["attachments"][0])


def _custom_field_search_filter(params: dict[str, str]) -> dict:
    return {
        "$all": [
            {"$elemMatch": {"name": name, "value": value}}
            for name, value in params.items()
        ]
    }


def _get_criteria_from_search_params(
    search_params: LogSearchParams,
) -> list[dict[str, Any]]:
    sp = search_params
    criteria = []
    if sp.action_type:
        criteria.append({"action.type": sp.action_type})
    if sp.action_category:
        criteria.append({"action.category": sp.action_category})
    if sp.source:
        criteria.append({"source": _custom_field_search_filter(sp.source)})
    if sp.actor_type:
        criteria.append({"actor.type": sp.actor_type})
    if sp.actor_name:
        criteria.append({"actor.name": sp.actor_name})
    if sp.actor_ref:
        criteria.append({"actor.ref": sp.actor_ref})
    if sp.actor_extra:
        criteria.append({"actor.extra": _custom_field_search_filter(sp.actor_extra)})
    if sp.resource_type:
        criteria.append({"resource.type": sp.resource_type})
    if sp.resource_name:
        criteria.append({"resource.name": sp.resource_name})
    if sp.resource_ref:
        criteria.append({"resource.ref": sp.resource_ref})
    if sp.resource_extra:
        criteria.append(
            {"resource.extra": _custom_field_search_filter(sp.resource_extra)}
        )
    if sp.details:
        criteria.append({"details": _custom_field_search_filter(sp.details)})
    if sp.tag_ref:
        criteria.append({"tags.ref": sp.tag_ref})
    if sp.tag_type:
        criteria.append({"tags.type": sp.tag_type})
    if sp.tag_name:
        criteria.append({"tags.name": sp.tag_name})
    if sp.has_attachment is not None:
        if sp.has_attachment:
            criteria.append({"attachments": {"$not": {"$size": 0}}})
        else:
            criteria.append({"attachments": {"$size": 0}})
    if sp.attachment_name:
        criteria.append({"attachments.name": sp.attachment_name})
    if sp.attachment_type:
        criteria.append({"attachments.type": sp.attachment_type})
    if sp.attachment_mime_type:
        criteria.append({"attachments.mime_type": sp.attachment_mime_type})
    if sp.entity_ref:
        criteria.append({"entity_path.ref": sp.entity_ref})
    if sp.since:
        criteria.append({"saved_at": {"$gte": sp.since}})
    if sp.until:
        # don't want to miss logs saved at the same second, meaning that the "until: ...23:59:59" criterion
        # will also include logs saved at 23:59:59.500 for instance
        criteria.append({"saved_at": {"$lte": sp.until.replace(microsecond=999999)}})
    return criteria


class _LogsPaginationCursor:
    def __init__(self, date: datetime, id: uuid.UUID):
        self.date = date
        self.id = id

    @classmethod
    def load(cls, value: str) -> "_LogsPaginationCursor":
        decoded = load_pagination_cursor(value)

        try:
            return cls(
                datetime.fromisoformat(decoded["date"]), uuid.UUID(decoded["id"])
            )
        except (KeyError, ValueError):
            raise InvalidPaginationCursor(value)

    def serialize(self) -> str:
        return serialize_pagination_cursor(
            {
                "date": serialize_datetime(self.date, with_milliseconds=True),
                "id": str(self.id),
            }
        )


async def _get_logs_paginated(
    log_db: LogDatabase,
    *,
    id_field,
    date_field,
    filter=None,
    projection=None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list[Log], str | None]:
    if filter is None:
        filter = {}

    if pagination_cursor:
        cursor = _LogsPaginationCursor.load(pagination_cursor)
        filter = {  # noqa
            "$and": [
                filter,
                {"saved_at": {"$lte": cursor.date}},
                {
                    "$or": [
                        {"saved_at": {"$lt": cursor.date}},
                        {"_id": {"$lt": cursor.id}},
                    ]
                },
            ]
        }

    results = await log_db.logs.find(
        filter, projection, sort=[(date_field, -1), (id_field, -1)], limit=limit + 1
    ).to_list(None)

    # we previously fetched one extra log to check if there are more logs to fetch
    if len(results) == limit + 1:
        # there is still more logs to fetch, so we need to return a next_cursor based on the last log WITHIN the
        # limit range
        next_cursor_obj = _LogsPaginationCursor(
            results[-2][date_field], results[-2][id_field]
        )
        next_cursor = next_cursor_obj.serialize()
        # remove the extra log
        results.pop(-1)
    else:
        next_cursor = None

    return [Log(**result) for result in results], next_cursor


async def get_logs(
    repo: UUID | LogDatabase,
    *,
    authorized_entities: set[str] = None,
    search_params: LogSearchParams = None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list[Log], str | None]:
    if isinstance(repo, LogDatabase):
        db = repo
    else:
        db = await get_log_db_for_reading(repo)

    criteria: list[dict[str, Any]] = []
    if authorized_entities:
        criteria.append({"entity_path.ref": {"$in": list(authorized_entities)}})
    if search_params:
        criteria.extend(_get_criteria_from_search_params(search_params))

    return await _get_logs_paginated(
        db,
        id_field="_id",
        date_field="saved_at",
        projection=_EXCLUDE_ATTACHMENT_DATA,
        filter={"$and": criteria} if criteria else None,
        limit=limit,
        pagination_cursor=pagination_cursor,
    )


async def _apply_log_retention_period(repo: Repo):
    if not repo.retention_period:
        return

    db = await get_log_db_for_maintenance(repo)
    result = await db.logs.delete_many(
        {"saved_at": {"$lt": now() - timedelta(days=repo.retention_period)}}
    )
    if result.deleted_count > 0:
        print(
            f"Deleted {result.deleted_count} logs older than {repo.retention_period} days "
            f"in log repository {repo.name!r}"
        )


async def apply_log_retention_period(repo: UUID | Repo = None):
    if repo:
        repos = [await get_repo(repo)]
    else:
        repos = await get_retention_period_enabled_repos()

    for repo in repos:
        await _apply_log_retention_period(repo)
        await purge_orphan_consolidated_log_data(repo)
