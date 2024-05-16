import re
from datetime import datetime
from functools import partial
from typing import Any

from auditize.database import DatabaseManager
from auditize.exceptions import UnknownModelException
from auditize.helpers.pagination.cursor.service import find_paginated_by_cursor
from auditize.helpers.pagination.page.models import PagePaginationInfo
from auditize.helpers.pagination.page.service import find_paginated_by_page
from auditize.helpers.resources.service import (
    create_resource_document,
    get_resource_document,
    update_resource_document,
)
from auditize.logs.db import LogDatabase, get_log_db
from auditize.logs.models import CustomField, Log, Node

# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}


async def consolidate_log_action(db: LogDatabase, action: Log.Action):
    await db.consolidate_data(
        db.log_actions, {"category": action.category, "type": action.type}
    )


async def consolidate_log_source(db: LogDatabase, source: list[CustomField]):
    for field in source:
        await db.consolidate_data(db.log_source_fields, {"name": field.name})


async def consolidate_log_actor(db: LogDatabase, actor: Log.Actor):
    await db.consolidate_data(db.log_actor_types, {"type": actor.type})
    for field in actor.extra:
        await db.consolidate_data(db.log_actor_extra_fields, {"name": field.name})


async def consolidate_log_resource(db: LogDatabase, resource: Log.Resource):
    await db.consolidate_data(db.log_resource_types, {"type": resource.type})
    for field in resource.extra:
        await db.consolidate_data(db.log_resource_extra_fields, {"name": field.name})


async def consolidate_log_tags(db: LogDatabase, tags: list[Log.Tag]):
    for tag in tags:
        await db.consolidate_data(db.log_tag_types, {"type": tag.type})


async def consolidate_log_details(db: LogDatabase, details: list[CustomField]):
    for field in details:
        await db.consolidate_data(db.log_detail_fields, {"name": field.name})


async def consolidate_log_node_path(db: LogDatabase, node_path: list[Log.Node]):
    parent_node_ref = None
    for node in node_path:
        await db.consolidate_data(
            db.log_nodes,
            {"parent_node_ref": parent_node_ref, "ref": node.ref, "name": node.name},
        )
        parent_node_ref = node.ref


async def save_log(dbm: DatabaseManager, repo_id: str, log: Log) -> str:
    db = await get_log_db(dbm, repo_id)

    log_id = await create_resource_document(db.logs, log)

    await consolidate_log_action(db, log.action)

    await consolidate_log_source(db, log.source)

    if log.actor:
        await consolidate_log_actor(db, log.actor)

    if log.resource:
        await consolidate_log_resource(db, log.resource)

    await consolidate_log_details(db, log.details)

    await consolidate_log_tags(db, log.tags)

    await consolidate_log_node_path(db, log.node_path)

    return log_id


async def save_log_attachment(
    dbm: DatabaseManager,
    repo_id: str,
    log_id: str,
    *,
    name: str,
    description: str,
    type: str,
    mime_type: str,
    data: bytes,
):
    db = await get_log_db(dbm, repo_id)
    await update_resource_document(
        db.logs,
        log_id,
        {
            "attachments": {
                "name": name,
                "description": description,
                "type": type,
                "mime_type": mime_type,
                "data": data,
            }
        },
        operator="$push",
    )


async def get_log(dbm: DatabaseManager, repo_id: str, log_id: str) -> Log:
    db = await get_log_db(dbm, repo_id)
    document = await get_resource_document(
        db.logs, log_id, projection=_EXCLUDE_ATTACHMENT_DATA
    )
    return Log.model_validate(document)


async def get_log_attachment(
    dbm: DatabaseManager, repo_id: str, log_id: str, attachment_idx: int
) -> Log.Attachment:
    db = await get_log_db(dbm, repo_id)
    doc = await get_resource_document(
        db.logs, log_id, projection={"attachments": {"$slice": [attachment_idx, 1]}}
    )
    if len(doc["attachments"]) == 0:
        raise UnknownModelException()
    return Log.Attachment(**doc["attachments"][0])


def _text_search_filter(text: str) -> dict[str, Any]:
    return {"$regex": re.compile(re.escape(text), re.IGNORECASE)}


def _custom_field_search_filter(params: dict[str, str]) -> dict:
    return {
        "$all": [
            {"$elemMatch": {"name": name, "value": _text_search_filter(value)}}
            for name, value in params.items()
        ]
    }


async def get_logs(
    dbm: DatabaseManager,
    repo_id: str,
    *,
    action_type: str = None,
    action_category: str = None,
    actor_type: str = None,
    actor_name: str = None,
    actor_extra: dict = None,
    resource_type: str = None,
    resource_name: str = None,
    details: dict = None,
    source: dict = None,
    tag_ref: str = None,
    tag_type: str = None,
    tag_name: str = None,
    node_ref: str = None,
    since: datetime = None,
    until: datetime = None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list[Log], str | None]:
    db = await get_log_db(dbm, repo_id)

    criteria: dict[str, Any] = {}
    if action_type:
        criteria["action.type"] = action_type
    if action_category:
        criteria["action.category"] = action_category
    if source:
        criteria["source"] = _custom_field_search_filter(source)
    if actor_type:
        criteria["actor.type"] = actor_type
    if actor_name:
        criteria["actor.name"] = _text_search_filter(actor_name)
    if actor_extra:
        criteria["actor.extra"] = _custom_field_search_filter(actor_extra)
    if resource_type:
        criteria["resource.type"] = resource_type
    if resource_name:
        criteria["resource.name"] = _text_search_filter(resource_name)
    if details:
        criteria["details"] = _custom_field_search_filter(details)
    if tag_ref:
        criteria["tags.ref"] = tag_ref
    if tag_type:
        criteria["tags.type"] = tag_type
    if tag_name:
        criteria["tags.name"] = _text_search_filter(tag_name)
    if node_ref:
        criteria["node_path.ref"] = node_ref
    if since:
        criteria["saved_at"] = {"$gte": since}
    if until:
        criteria["saved_at"] = {
            # do not overwrite "since" criterion if any:
            **criteria.get("saved_at", {}),
            # don't want to miss logs saved at the same second, meaning that the "until: ...23:59:59" criterion
            # will also include logs saved at 23:59:59.500 for instance
            "$lte": until.replace(microsecond=999999),
        }

    results, next_cursor = await find_paginated_by_cursor(
        db.logs,
        id_field="_id",
        date_field="saved_at",
        projection=_EXCLUDE_ATTACHMENT_DATA,
        filter=criteria,
        limit=limit,
        pagination_cursor=pagination_cursor,
    )

    logs = [Log(**result) for result in results]

    return logs, next_cursor


async def _get_consolidated_data_aggregated_field(
    dbm: DatabaseManager,
    repo_id: str,
    collection_name: str,
    field_name: str,
    *,
    match=None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    # Get all unique aggregated data field
    db = await get_log_db(dbm, repo_id)
    collection = db.get_collection(collection_name)
    results = collection.aggregate(
        ([{"$match": match}] if match else [])
        + [
            {"$group": {"_id": "$" + field_name}},
            {"$sort": {"_id": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
        ]
    )
    values = [result["_id"] async for result in results]

    # Get the total number of unique aggregated field value
    results = collection.aggregate(
        ([{"$match": match}] if match else [])
        + [{"$group": {"_id": "$" + field_name}}, {"$count": "total"}]
    )
    try:
        total = (await results.next())["total"]
    except StopAsyncIteration:
        total = 0

    return values, PagePaginationInfo.build(page=page, page_size=page_size, total=total)


async def _get_consolidated_data_field(
    dbm: DatabaseManager,
    repo_id,
    collection_name,
    field_name: str,
    *,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_log_db(dbm, repo_id)
    results, pagination = await find_paginated_by_page(
        db.get_collection(collection_name),
        projection=[field_name],
        sort={field_name: 1},
        page=page,
        page_size=page_size,
    )
    return [result[field_name] async for result in results], pagination


get_log_action_categories = partial(
    _get_consolidated_data_aggregated_field,
    collection_name="log_actions",
    field_name="category",
)


async def get_log_action_types(
    dbm: DatabaseManager,
    repo_id: str,
    *,
    action_category: str = None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    return await _get_consolidated_data_aggregated_field(
        dbm,
        repo_id,
        collection_name="log_actions",
        field_name="type",
        page=page,
        page_size=page_size,
        match={"category": action_category} if action_category else None,
    )


get_log_actor_types = partial(
    _get_consolidated_data_field,
    collection_name="log_actor_types",
    field_name="type",
)

get_log_actor_extra_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_actor_extra_fields",
    field_name="name",
)

get_log_resource_types = partial(
    _get_consolidated_data_field,
    collection_name="log_resource_types",
    field_name="type",
)

get_log_resource_extra_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_resource_extra_fields",
    field_name="name",
)

get_log_tag_types = partial(
    _get_consolidated_data_field,
    collection_name="log_tag_types",
    field_name="type",
)

get_log_source_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_source_fields",
    field_name="name",
)

get_log_detail_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_detail_fields",
    field_name="name",
)


async def _get_log_nodes(db: LogDatabase, *, match, pipeline_extra=None):
    return db.log_nodes.aggregate(
        [
            {"$match": match},
            {
                "$lookup": {
                    "from": "log_nodes",
                    "let": {"ref": "$ref"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$parent_node_ref", "$$ref"]}}},
                        {"$limit": 1},
                    ],
                    "as": "first_child_if_any",
                }
            },
            {
                "$addFields": {
                    "has_children": {"$eq": [{"$size": "$first_child_if_any"}, 1]}
                }
            },
        ]
        + (pipeline_extra or [])
    )


async def get_log_nodes(
    dbm: DatabaseManager,
    repo_id: str,
    *,
    parent_node_ref=NotImplemented,
    page=1,
    page_size=10,
) -> tuple[list[Log.Node], PagePaginationInfo]:
    db = await get_log_db(dbm, repo_id)

    # please note that we use NotImplemented instead of None because None is a valid value for parent_node_ref
    # (it means filtering on top nodes)
    if parent_node_ref is NotImplemented:
        filter = {}
    else:
        filter = {"parent_node_ref": parent_node_ref}

    results = await _get_log_nodes(
        db,
        match=filter,
        pipeline_extra=[
            {"$sort": {"name": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
        ],
    )

    total = await db.log_nodes.count_documents(filter or {})

    return (
        [Node(**result) async for result in results],
        PagePaginationInfo.build(page=page, page_size=page_size, total=total),
    )


async def get_log_node(dbm: DatabaseManager, repo_id: str, node_ref: str) -> Log.Node:
    db = await get_log_db(dbm, repo_id)

    results = await (await _get_log_nodes(db, match={"ref": node_ref})).to_list(None)
    try:
        result = results[0]
    except IndexError:
        raise UnknownModelException(node_ref)

    return Node(**result)
