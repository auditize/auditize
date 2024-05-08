import re
from datetime import datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.common.pagination.cursor.service import find_paginated_by_cursor
from auditize.common.pagination.page.models import PagePaginationInfo
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.database import DatabaseManager
from auditize.exceptions import UnknownModelException
from auditize.logs.db import LogsDatabase, get_logs_db
from auditize.logs.models import Log, Node

# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}


async def consolidate_log_event(db: LogsDatabase, event: Log.Event):
    await db.consolidate_data(
        db.log_events, {"category": event.category, "name": event.name}
    )


async def consolidate_log_actor(db: LogsDatabase, actor: Log.Actor):
    await db.consolidate_data(db.log_actor_types, {"type": actor.type})
    for key in actor.extra:
        await db.consolidate_data(db.log_actor_extra_keys, {"key": key})


async def consolidate_log_resource(db: LogsDatabase, resource: Log.Resource):
    await db.consolidate_data(db.log_resource_types, {"type": resource.type})
    for key in resource.extra:
        await db.consolidate_data(db.log_resource_extra_keys, {"key": key})


async def consolidate_log_tags(db: LogsDatabase, tags: list[Log.Tag]):
    for tag in tags:
        if tag.category:
            await db.consolidate_data(db.log_tag_categories, {"category": tag.category})


async def consolidate_log_details(db: LogsDatabase, details: dict[str, dict[str, str]]):
    for level1_key, sub_keys in details.items():
        for level2_key in sub_keys:
            await db.consolidate_data(
                db.log_detail_keys, {"level1_key": level1_key, "level2_key": level2_key}
            )


async def consolidate_log_node_path(db: LogsDatabase, node_path: list[Log.Node]):
    parent_node_id = None
    for node in node_path:
        await db.consolidate_data(
            db.log_nodes,
            {"parent_node_id": parent_node_id, "id": node.id, "name": node.name},
        )
        parent_node_id = node.id


async def save_log(dbm: DatabaseManager, repo_id: str, log: Log) -> ObjectId:
    db = await get_logs_db(dbm, repo_id)

    result = await db.logs.insert_one(log.model_dump(exclude={"id"}))

    await consolidate_log_event(db, log.event)

    for key in log.source:
        await db.consolidate_data(db.log_source_keys, {"key": key})

    if log.actor:
        await consolidate_log_actor(db, log.actor)

    if log.resource:
        await consolidate_log_resource(db, log.resource)

    await consolidate_log_details(db, log.details)

    await consolidate_log_tags(db, log.tags)

    await consolidate_log_node_path(db, log.node_path)

    return result.inserted_id


async def save_log_attachment(
    dbm: DatabaseManager,
    repo_id: str,
    log_id: ObjectId | str,
    name: str,
    type: str,
    mime_type: str,
    data: bytes,
):
    db = await get_logs_db(dbm, repo_id)

    await db.logs.update_one(
        {"_id": ObjectId(log_id)},
        {
            "$push": {
                "attachments": {
                    "name": name,
                    "type": type,
                    "mime_type": mime_type,
                    "data": data,
                }
            }
        },
    )


async def get_log(dbm: DatabaseManager, repo_id: str, log_id: ObjectId | str) -> Log:
    db = await get_logs_db(dbm, repo_id)

    data = await db.logs.find_one(ObjectId(log_id), _EXCLUDE_ATTACHMENT_DATA)
    if data is None:
        raise UnknownModelException(log_id)
    return Log(**data)


async def get_log_attachment(
    dbm: DatabaseManager, repo_id: str, log_id: ObjectId | str, attachment_idx: int
) -> Log.Attachment:
    db = await get_logs_db(dbm, repo_id)

    result = await db.logs.find_one(
        {"_id": ObjectId(log_id)},
        {"attachments": {"$slice": [attachment_idx, 1]}},
    )
    if result is None or len(result["attachments"]) == 0:
        raise UnknownModelException()
    return Log.Attachment(**result["attachments"][0])


def _text_search_filter(text: str) -> dict[str, Any]:
    return {"$regex": re.compile(re.escape(text), re.IGNORECASE)}


async def get_logs(
    dbm: DatabaseManager,
    repo_id: str,
    *,
    event_name: str = None,
    event_category: str = None,
    actor_type: str = None,
    actor_name: str = None,
    resource_type: str = None,
    resource_name: str = None,
    tag_category: str = None,
    tag_name: str = None,
    tag_id: str = None,
    node_id: str = None,
    since: datetime = None,
    until: datetime = None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list[Log], str | None]:
    db = await get_logs_db(dbm, repo_id)

    criteria = {}
    if event_name:
        criteria["event.name"] = event_name
    if event_category:
        criteria["event.category"] = event_category
    if actor_type:
        criteria["actor.type"] = actor_type
    if actor_name:
        criteria["actor.name"] = _text_search_filter(actor_name)
    if resource_type:
        criteria["resource.type"] = resource_type
    if resource_name:
        criteria["resource.name"] = _text_search_filter(resource_name)
    if tag_category:
        criteria["tags.category"] = tag_category
    if tag_name:
        criteria["tags.name"] = _text_search_filter(tag_name)
    if tag_id:
        criteria["tags.id"] = tag_id
    if node_id:
        criteria["node_path.id"] = node_id
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
        filter=criteria,
        limit=limit,
        pagination_cursor=pagination_cursor,
    )

    logs = [Log(**result) for result in results]

    return logs, next_cursor


async def _get_consolidated_data_aggregated_field(
    collection: AsyncIOMotorCollection,
    field_name: str,
    *,
    match=None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    # Get all unique aggregated data field
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
    collection: AsyncIOMotorCollection, field_name: str, *, page=1, page_size=10
) -> tuple[list[str], PagePaginationInfo]:
    results, pagination = await find_paginated_by_page(
        collection,
        projection=[field_name],
        sort={field_name: 1},
        page=page,
        page_size=page_size,
    )
    return [result[field_name] async for result in results], pagination


async def get_log_event_categories(
    dbm: DatabaseManager, repo_id: str, *, page=1, page_size=10
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_logs_db(dbm, repo_id)
    return await _get_consolidated_data_aggregated_field(
        db.log_events, "category", page=page, page_size=page_size
    )


async def get_log_events(
    dbm: DatabaseManager,
    repo_id: str,
    *,
    event_category: str = None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_logs_db(dbm, repo_id)
    return await _get_consolidated_data_aggregated_field(
        db.log_events,
        "name",
        page=page,
        page_size=page_size,
        match={"category": event_category} if event_category else None,
    )


async def get_log_actor_types(
    dbm: DatabaseManager, repo_id: str, *, page=1, page_size=10
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_logs_db(dbm, repo_id)
    return await _get_consolidated_data_field(
        db.log_actor_types, "type", page=page, page_size=page_size
    )


async def get_log_resource_types(
    dbm: DatabaseManager, repo_id: str, *, page=1, page_size=10
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_logs_db(dbm, repo_id)
    return await _get_consolidated_data_field(
        db.log_resource_types, "type", page=page, page_size=page_size
    )


async def get_log_tag_categories(
    dbm: DatabaseManager, repo_id: str, *, page=1, page_size=10
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_logs_db(dbm, repo_id)
    return await _get_consolidated_data_field(
        db.log_tag_categories, "category", page=page, page_size=page_size
    )


async def _get_log_nodes(db: LogsDatabase, *, match, pipeline_extra=None):
    return db.log_nodes.aggregate(
        [
            {"$match": match},
            {
                "$lookup": {
                    "from": "log_nodes",
                    "let": {"id": "$id"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$parent_node_id", "$$id"]}}},
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
    parent_node_id=NotImplemented,
    page=1,
    page_size=10,
) -> tuple[list[Log.Node], PagePaginationInfo]:
    db = await get_logs_db(dbm, repo_id)

    # please note that we use NotImplemented instead of None because None is a valid value for parent_node_id
    # (it means filtering on top nodes)
    if parent_node_id is NotImplemented:
        filter = {}
    else:
        filter = {"parent_node_id": parent_node_id}

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


async def get_log_node(dbm: DatabaseManager, repo_id: str, node_id: str) -> Log.Node:
    db = await get_logs_db(dbm, repo_id)

    results = await (await _get_log_nodes(db, match={"id": node_id})).to_list(None)
    try:
        result = results[0]
    except IndexError:
        raise UnknownModelException(node_id)

    return Node(**result)
