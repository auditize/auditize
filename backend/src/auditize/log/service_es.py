import base64
import os
import uuid
from datetime import timedelta
from typing import Any
from uuid import UUID

from elasticsearch import AsyncElasticsearch

from auditize.exceptions import (
    UnknownModelException,
)
from auditize.helpers.datetime import now
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
from auditize.resource.pagination.cursor.service import find_paginated_by_cursor
from auditize.resource.service import (
    create_resource_document,
    get_resource_document,
    update_resource_document,
)

from .service import CSV_BUILTIN_COLUMNS

# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}


def get_es_client():
    return AsyncElasticsearch(
        "https://localhost:9200",
        verify_certs=False,
        basic_auth=("elastic", os.environ["ES_PASSWORD"]),
    )


async def save_log(repo_id: UUID, log: Log) -> UUID:
    es = get_es_client()
    log_id = uuid.uuid4()
    await es.index(
        index=f"auditize_logs_{repo_id}",
        id=str(log_id),
        document=log.model_dump(exclude={"id"}),
    )
    return log_id


async def save_log_attachment(
    repo_id: UUID,
    log_id: UUID,
    *,
    name: str,
    type: str,
    mime_type: str,
    data: bytes,
):
    es = get_es_client()
    attachment = Log.Attachment(name=name, type=type, mime_type=mime_type, data=data)

    await es.update(
        index=f"auditize_logs_{repo_id}",
        id=str(log_id),
        script={
            "source": "ctx._source.attachments.add(params.attachment)",
            "params": {
                "attachment": {
                    **attachment.model_dump(exclude={"data"}),
                    "data": base64.b64encode(data).decode(),
                }
            },
        },
    )


async def get_log(repo_id: UUID, log_id: UUID, authorized_entities: set[str]) -> Log:
    es = get_es_client()
    filter = {"_id": str(log_id)}
    if authorized_entities:
        filter["entity_path.ref"] = list(authorized_entities)

    resp = await es.search(
        index=f"auditize_logs_{repo_id}",
        query={
            "bool": {
                "filter": [{"term": {field: value} for field, value in filter.items()}]
            }
        },
        source_excludes=["attachments.data"],
    )
    documents = resp["hits"]["hits"]
    if not documents:
        raise UnknownModelException()

    model = Log.model_validate({**documents[0]["_source"], "_id": log_id})
    return model


async def get_log_attachment(
    repo_id: UUID, log_id: UUID, attachment_idx: int
) -> Log.Attachment:
    es = get_es_client()

    # NB: we retrieve all attachments here, which is not really efficient is the log contains
    # more than 1 log, unfortunately ES does not a let us retrieve a nested object to a specific
    # array index unless adding an extra metadata such as "index" to the stored document
    resp = await es.get(
        index=f"auditize_logs_{repo_id}",
        id=str(log_id),
        source_includes=["attachments"],
    )
    if not resp["found"]:
        raise UnknownModelException()

    try:
        attachment = resp["_source"]["attachments"][attachment_idx]
    except IndexError:
        raise UnknownModelException()

    return Log.Attachment.model_validate(
        {**attachment, "data": base64.b64decode(attachment["data"])}
    )


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

    results, next_cursor = await find_paginated_by_cursor(
        db.logs,
        id_field="_id",
        date_field="saved_at",
        projection=_EXCLUDE_ATTACHMENT_DATA,
        filter={"$and": criteria} if criteria else None,
        limit=limit,
        pagination_cursor=pagination_cursor,
    )

    logs = [Log(**result) for result in results]

    return logs, next_cursor


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


async def create_index(repo_id: UUID):
    es = get_es_client()
    await es.indices.create(
        index=f"auditize_logs_{repo_id}",
        mappings={
            "properties": {
                "saved_at": {"type": "date"},
                "action": {
                    "properties": {
                        "type": {"type": "keyword"},
                        "category": {"type": "keyword"},
                    }
                },
                "source": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "keyword"},
                        "value": {"type": "text"},
                    },
                },
                "actor": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {"type": "text"},
                        "extra": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {"type": "text"},
                            },
                        },
                    }
                },
                "resource": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {"type": "text"},
                        "extra": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {"type": "text"},
                            },
                        },
                    }
                },
                "details": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "keyword"},
                        "value": {"type": "text"},
                    },
                },
                "tags": {
                    "type": "nested",
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {"type": "text"},
                    },
                },
                "attachments": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "text"},
                        "type": {"type": "keyword"},
                        "mime_type": {"type": "keyword"},
                        "saved_at": {"type": "date"},
                        "data": {"type": "binary"},
                    },
                },
                "entity_path": {
                    "type": "nested",
                    "properties": {
                        "ref": {"type": "keyword"},
                        "name": {"type": "text"},
                    },
                },
            }
        },
    )
