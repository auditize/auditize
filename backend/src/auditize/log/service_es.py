import base64
import binascii
import json
import os
import uuid
from datetime import datetime, timedelta
from functools import partial
from typing import Any
from uuid import UUID

import elasticsearch
from aiocache import Cache
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
    InvalidPaginationCursor,
    PaginationCursor,
    find_paginated_by_cursor,
)
from auditize.resource.service import (
    create_resource_document,
    get_resource_document,
    update_resource_document,
)

from ..resource.pagination.page.models import PagePaginationInfo
from .service import CSV_BUILTIN_COLUMNS, get_logs_as_csv, validate_csv_columns

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
    index = f"auditize_logs_{repo_id}"
    log_id = uuid.uuid4()
    await es.index(
        index=index,
        id=str(log_id),
        document={
            **log.model_dump(exclude={"id"}),
            "saved_at": serialize_datetime(log.saved_at, with_milliseconds=True),
            "id": log_id,
        },
    )
    await _consolidate_log_entity_path(index, log.entity_path)
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
                            {"term": {f"{type}.value.keyword": value}},
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
        filter.append({"term": {"actor.name.keyword": sp.actor_name}})
    if sp.actor_ref:
        filter.append({"term": {"actor.ref": sp.actor_ref}})
    if sp.actor_extra:
        filter.extend(_custom_field_search_filter("actor.extra", sp.actor_extra))
    if sp.resource_type:
        filter.append({"term": {"resource.type": sp.resource_type}})
    if sp.resource_name:
        filter.append({"term": {"resource.name.keyword": sp.resource_name}})
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
        filter.append(_nested_filter_term("tags", "tags.name.keyword", sp.tag_name))
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
            _nested_filter_term(
                "attachments", "attachments.name.keyword", sp.attachment_name
            )
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

    search_after = None
    if pagination_cursor:
        cursor = AfterPaginationCursor.load(pagination_cursor)
        search_after = cursor.after

    query = {"bool": {"filter": filter}}
    print("QUERY: %s" % json.dumps(query, default=str))
    resp = await es.search(
        index=f"auditize_logs_{repo}",
        query=query,
        search_after=search_after,
        source_excludes=["attachments.data"],
        sort=[{"saved_at": "desc", "id": "desc"}],
        size=limit + 1,
        track_total_hits=False,
    )
    print("RESPONSE: %s" % json.dumps(dict(resp), default=str))
    hits = list(resp["hits"]["hits"])

    # we previously fetched one extra log to check if there are more logs to fetch
    if len(hits) == limit + 1:
        # there is still more logs to fetch, so we need to return a next_cursor based on the last log WITHIN the
        # limit range
        next_cursor_obj = AfterPaginationCursor(hits[-2]["sort"])
        next_cursor = next_cursor_obj.serialize()
        hits.pop(-1)
    else:
        next_cursor = None

    logs = [
        Log.model_validate({**hit["_source"], "_id": hit["_source"]["id"]})
        for hit in hits
    ]

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
                        "value": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "actor": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "extra": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {
                                    "type": "text",
                                    "fields": {"keyword": {"type": "keyword"}},
                                },
                            },
                        },
                    }
                },
                "resource": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "extra": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {
                                    "type": "text",
                                    "fields": {"keyword": {"type": "keyword"}},
                                },
                            },
                        },
                    }
                },
                "details": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "keyword"},
                        "value": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "tags": {
                    "type": "nested",
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "attachments": {
                    "type": "nested",
                    "properties": {
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
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
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
            }
        },
        settings={
            "index": {
                "sort.field": ["saved_at", "id"],
                "sort.order": ["desc", "desc"],
            }
        },
    )


async def _empty_agg(*args, **kwargs):
    return [], PagePaginationInfo.build(1, 10, 0)


get_log_entities = _empty_agg


class AfterPaginationCursor:
    def __init__(self, after):
        self.after = after

    @classmethod
    def load(cls, value: str) -> "AfterPaginationCursor":
        try:
            decoded = json.loads(base64.b64decode(value).decode("utf-8"))
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
            raise InvalidPaginationCursor(value)

        try:
            return cls(decoded)
        except (KeyError, ValueError):
            raise InvalidPaginationCursor(value)

    def serialize(self) -> str:
        return base64.b64encode(json.dumps(self.after).encode("utf-8")).decode("utf-8")


async def _get_paginated_agg(
    repo_id: UUID,
    *,
    nested: str = None,
    field: str,
    query: dict = None,
    limit: int,
    pagination_cursor: str | None,
) -> tuple[list[str], str]:
    if pagination_cursor:
        cursor = AfterPaginationCursor.load(pagination_cursor)
        after = cursor.after
    else:
        after = None

    aggregations = {
        "group_by": {
            "composite": {
                "size": limit,
                "sources": [{field: {"terms": {"field": field, "order": "asc"}}}],
                **({"after": after} if after else {}),
            }
        },
    }
    if nested:
        aggregations = {
            "nested_group_by": {
                "nested": {
                    "path": nested,
                },
                "aggs": aggregations,
            },
        }

    print("REQUEST: %s" % json.dumps(aggregations))
    resp = await es.search(
        index=f"auditize_logs_{repo_id}",
        query=query,
        aggregations=aggregations,
        size=0,
    )

    print("RESPONSE: %s" % json.dumps(dict(resp)))

    if nested:
        group_by_result = resp["aggregations"]["nested_group_by"]["group_by"]
    else:
        group_by_result = resp["aggregations"]["group_by"]

    if len(group_by_result["buckets"]) == limit and "after_key" in group_by_result:
        next_cursor = AfterPaginationCursor(group_by_result["after_key"])
        next_cursor_raw = next_cursor.serialize()
    else:
        next_cursor_raw = None

    values = [bucket["key"][field] for bucket in group_by_result["buckets"]]

    return values, next_cursor_raw


get_log_action_categories = partial(_get_paginated_agg, field="action.category")


async def get_log_action_types(
    repo_id: UUID,
    action_category: str | None,
    limit: int,
    pagination_cursor: str | None,
) -> tuple[list[str], str]:
    return await _get_paginated_agg(
        repo_id,
        field="action.type",
        query=(
            {"bool": {"filter": {"term": {"action.category": action_category}}}}
            if action_category
            else None
        ),
        limit=limit,
        pagination_cursor=pagination_cursor,
    )


get_log_tag_types = partial(_get_paginated_agg, nested="tags", field="tags.type")


get_log_actor_types = partial(_get_paginated_agg, field="actor.type")


get_log_actor_extra_fields = partial(
    _get_paginated_agg, nested="actor.extra", field="actor.extra.name"
)


get_log_resource_types = partial(_get_paginated_agg, field="resource.type")


get_log_resource_extra_fields = partial(
    _get_paginated_agg, nested="resource.extra", field="resource.extra.name"
)


get_log_source_fields = partial(
    _get_paginated_agg, nested="source", field="source.name"
)


get_log_detail_fields = partial(
    _get_paginated_agg, nested="details", field="details.name"
)

get_log_attachment_types = partial(
    _get_paginated_agg, nested="attachments", field="attachments.type"
)

get_log_attachment_mime_types = partial(
    _get_paginated_agg, nested="attachments", field="attachments.mime_type"
)


_CONSOLIDATED_LOG_ENTITIES = Cache(Cache.MEMORY)


async def _consolidate_log_entity(
    index: str, entity: Log.Entity, parent_entity: Log.Entity | None
):
    doc = {
        "ref": entity.ref,
        "name": entity.name,
        "parent_entity_ref": parent_entity.ref if parent_entity else None,
    }
    cache_key = "%s:%s" % (index, doc.values())
    if await _CONSOLIDATED_LOG_ENTITIES.exists(cache_key):
        return

    try:
        await es.update(
            index=f"{index}_entities",
            id=entity.ref,
            doc=doc,
            doc_as_upsert=True,
        )
    except elasticsearch.ConflictError:
        # We may encounter a 409 error if two updates are made at the same time
        # just ignore those errors and mark the log entity as already consolidated.
        # It assumes that the being log entity being updated was the same as the one
        # we attempted to index.
        print(
            f"Detected conflict error while consolidating entity {entity.ref}, skip it."
        )
    await _CONSOLIDATED_LOG_ENTITIES.set(cache_key, True)


async def _consolidate_log_entity_path(index: str, entity_path: list[Log.Entity]):
    parent_entity = None
    for entity in entity_path:
        await _consolidate_log_entity(index, entity, parent_entity)
        parent_entity = entity
