import base64
import os
import uuid
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from elasticsearch import AsyncElasticsearch

from auditize.exceptions import (
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
from auditize.resource.pagination.cursor.service import (
    PaginationCursor,
    find_paginated_by_cursor,
)
from auditize.resource.service import (
    create_resource_document,
    get_resource_document,
    update_resource_document,
)

from ..resource.pagination.page.models import PagePaginationInfo
from .service import CSV_BUILTIN_COLUMNS

# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}


def get_es_client():
    return AsyncElasticsearch(
        "https://localhost:9200",
        verify_certs=False,
        basic_auth=("elastic", os.environ["ES_PASSWORD"]),
    )


es = get_es_client()


async def save_log(repo_id: UUID, log: Log) -> UUID:
    log_id = uuid.uuid4()
    await es.index(
        index=f"auditize_logs_{repo_id}",
        id=str(log_id),
        document={
            **log.model_dump(exclude={"id"}),
            "saved_at": serialize_datetime(log.saved_at, with_milliseconds=True),
            "id": log_id,
        },
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


# def _custom_field_search_filter(params: dict[str, str]) -> dict:
#     return {
#         "$all": [
#             {"$elemMatch": {"name": name, "value": value}}
#             for name, value in params.items()
#         ]
#     }


def _custom_field_search_filter(type: str, fields: dict[str, str]):
    return [
        {
            "nested": {
                "path": type,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {f"{type}.name": name}},
                            {"term": {f"{type}.value": value}},
                        ]
                    }
                },
            }
        }
        for name, value in fields.items()
    ]


def _nested_filter_term(path, name, value):
    return {
        "nested": {
            "path": path,
            "query": {"bool": {"filter": [{"term": {name: value}}]}},
        }
    }


def _prepare_es_query(search_params: LogSearchParams) -> tuple[list[dict], list[dict]]:
    sp = search_params
    filter = []
    must_not = []
    if sp.action_type:
        filter.append({"term": {"action.type": sp.action_type}})
    if sp.action_category:
        filter.append({"term": {"action.category": sp.action_category}})
    if sp.source:
        filter.extend(_custom_field_search_filter("source", sp.source))
    if sp.actor_type:
        filter.append({"term": {"actor.type": sp.actor_type}})
    if sp.actor_name:
        filter.append({"term": {"actor.name": sp.actor_name}})
    if sp.actor_ref:
        filter.append({"term": {"actor.ref": sp.actor_ref}})
    if sp.actor_extra:
        filter.extend(_custom_field_search_filter("actor.extra", sp.actor_extra))
    if sp.resource_type:
        filter.append({"term": {"resource.type": sp.resource_type}})
    if sp.resource_name:
        filter.append({"term": {"resource.name": sp.resource_name}})
    if sp.resource_ref:
        filter.append({"term": {"resource.ref": sp.resource_ref}})
    if sp.resource_extra:
        filter.extend(_custom_field_search_filter("resource.extra", sp.resource_extra))
    if sp.details:
        filter.extend(_custom_field_search_filter("details", sp.details))
    if sp.tag_ref:
        filter.append(_nested_filter_term("tags", "tags.ref", sp.tag_ref))
    if sp.tag_type:
        filter.append(_nested_filter_term("tags", "tags.type", sp.tag_type))
    if sp.tag_name:
        filter.append(_nested_filter_term("tags", "tags.name", sp.tag_name))
    if sp.has_attachment is not None:
        if sp.has_attachment:
            filter.append(
                {
                    "nested": {
                        "path": "attachments",
                        "query": {"exists": {"field": "attachments"}},
                    }
                }
            )
        else:
            must_not.append({"exists": {"field": "attachments"}})
    if sp.attachment_name:
        filter.append(
            _nested_filter_term("attachments", "attachments.name", sp.attachment_name)
        )
    if sp.attachment_type:
        filter.append(
            _nested_filter_term("attachments", "attachments.type", sp.attachment_type)
        )
    if sp.attachment_mime_type:
        filter.append(
            _nested_filter_term(
                "attachments", "attachments.mime_type", sp.attachment_mime_type
            )
        )
    if sp.entity_ref:
        filter.append(
            _nested_filter_term("entity_path", "entity_path.ref", sp.entity_ref)
        )
    if sp.since:
        filter.append({"range": {"saved_at": {"gte": sp.since}}})
    if sp.until:
        # don't want to miss logs saved at the same second, meaning that the "until: ...23:59:59" criterion
        # will also include logs saved at 23:59:59.500 for instance
        filter.append(
            {"range": {"saved_at": {"lte": sp.until.replace(microsecond=999999)}}}
        )
    return filter, must_not


async def get_logs(
    repo: UUID | LogDatabase,
    *,
    search_params: LogSearchParams,
    authorized_entities: set[str] = None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list[Log], str | None]:
    filter, must_not = _prepare_es_query(search_params)
    should = []

    if authorized_entities:
        filter.append({"term": {"entity_path.ref": list(authorized_entities)}})

    if pagination_cursor:
        cursor = PaginationCursor.load(pagination_cursor)
        filter.append({"range": {"saved_at": {"lte": cursor.date}}})
        filter.append(
            {
                "bool": {
                    "should": [
                        {"range": {"saved_at": {"lt": cursor.date}}},
                        {"range": {"id": {"lt": cursor.id}}},
                    ]
                }
            }
        )

    query = {"bool": {"filter": filter, "must_not": must_not, "should": should}}
    print("QUERY: %s" % query)
    resp = await es.search(
        index=f"auditize_logs_{repo}",
        query=query,
        source_excludes=["attachments.data"],
        sort=[{"saved_at": "desc", "id": "desc"}],
        size=limit + 1,
    )
    hits = list(resp["hits"]["hits"])

    # we previously fetched one extra log to check if there are more logs to fetch
    if len(hits) == limit + 1:
        # there is still more logs to fetch, so we need to return a next_cursor based on the last log WITHIN the
        # limit range
        next_cursor_obj = PaginationCursor(
            datetime.fromisoformat(hits[-2]["_source"]["saved_at"]),
            uuid.UUID(hits[-2]["_source"]["id"]),
        )
        next_cursor = next_cursor_obj.serialize()
        hits.pop(-1)
    else:
        next_cursor = None

    logs = [
        Log.model_validate({**hit["_source"], "_id": hit["_source"]["id"]})
        for hit in hits
    ]

    print("RETURN: %s" % [(log.id, log.saved_at) for log in logs])

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
    await es.indices.create(
        index=f"auditize_logs_{repo_id}",
        mappings={
            "properties": {
                "id": {"type": "keyword"},
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


async def get_log_resource_extra_fields(*args, **kwargs):
    return [], PagePaginationInfo.build(1, 0, 0)
