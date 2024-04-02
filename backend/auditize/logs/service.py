from typing import Any
from datetime import datetime
import base64
import binascii

from bson import ObjectId
import json

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from auditize.logs.models import Log, Node, PaginationInfo
from auditize.common.mongo import Database
from auditize.common.exceptions import UnknownModelException
from auditize.common.utils import serialize_datetime


# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}


class InvalidPaginationCursor(Exception):
    pass


class PaginationCursor:
    def __init__(self, date: datetime, log_id: ObjectId):
        self.date = date
        self.log_id = log_id

    @classmethod
    def load(cls, value: str) -> "PaginationCursor":
        try:
            decoded = json.loads(base64.b64decode(value).decode("utf-8"))
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
            raise InvalidPaginationCursor(value)

        try:
            return cls(datetime.fromisoformat(decoded["date"]), ObjectId(decoded["log_id"]))
        except (KeyError, ValueError):
            raise InvalidPaginationCursor(value)

    def serialize(self) -> str:
        data = {"date": serialize_datetime(self.date, with_milliseconds=True), "log_id": str(self.log_id)}
        return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")


async def consolidate_log_event(db: Database, event: Log.Event):
    await db.consolidate_data(
        db.log_events, {"category": event.category, "name": event.name}
    )


async def consolidate_log_actor(db: Database, actor: Log.Actor):
    await db.consolidate_data(db.log_actor_types, {"type": actor.type})
    for key in actor.extra:
        await db.consolidate_data(db.log_actor_extra_keys, {"key": key})


async def consolidate_log_resource(db: Database, resource: Log.Resource):
    await db.consolidate_data(db.log_resource_types, {"type": resource.type})
    for key in resource.extra:
        await db.consolidate_data(db.log_resource_extra_keys, {"key": key})


async def consolidate_log_tags(db: Database, tags: list[Log.Tag]):
    for tag in tags:
        if tag.category:
            await db.consolidate_data(db.log_tag_categories, {"category": tag.category})


async def consolidate_log_details(db: Database, details: dict[str, dict[str, str]]):
    for level1_key, sub_keys in details.items():
        for level2_key in sub_keys:
            await db.consolidate_data(
                db.log_detail_keys, {"level1_key": level1_key, "level2_key": level2_key}
            )


async def consolidate_log_node_path(db: Database, node_path: list[Log.Node]):
    parent_node_id = None
    for node in node_path:
        await db.consolidate_data(db.log_nodes, {
            "parent_node_id": parent_node_id, "id": node.id, "name": node.name
        })
        parent_node_id = node.id


async def save_log(db: Database, log: Log) -> ObjectId:
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


async def save_log_attachment(db: Database, log_id: ObjectId | str, name: str, type: str, mime_type: str, data: bytes):
    await db.logs.update_one(
        {"_id": ObjectId(log_id)},
        {"$push": {"attachments": {"name": name, "type": type, "mime_type": mime_type, "data": data}}},
    )


async def get_log(db: Database, log_id: ObjectId | str) -> Log:
    data = await db.logs.find_one(ObjectId(log_id), _EXCLUDE_ATTACHMENT_DATA)
    if data is None:
        raise UnknownModelException(log_id)
    return Log(**data)


async def get_log_attachment(db: Database, log_id: ObjectId | str, attachment_idx: int) -> Log.Attachment:
    result = await db.logs.find_one(
        {"_id": ObjectId(log_id)},
        {"attachments": {"$slice": [attachment_idx, 1]}},
    )
    if result is None or len(result["attachments"]) == 0:
        raise UnknownModelException()
    return Log.Attachment(**result["attachments"][0])


async def get_logs(
    db: Database,
    *,
    event_name: str = None,
    event_category: str = None,
    actor_type: str = None, actor_name: str = None,
    resource_type: str = None, resource_name: str = None,
    tag_category: str = None, tag_name: str = None,
    node_id: str = None,
    limit: int = 10, pagination_cursor: str = None
   ) -> tuple[list[Log], str | None]:
    criteria = {}
    if event_name:
        criteria["event.name"] = event_name
    if event_category:
        criteria["event.category"] = event_category
    if actor_type:
        criteria["actor.type"] = actor_type
    if actor_name:
        criteria["actor.name"] = actor_name
    if resource_type:
        criteria["resource.type"] = resource_type
    if resource_name:
        criteria["resource.name"] = resource_name
    if tag_category:
        criteria["tags.category"] = tag_category
    if tag_name:
        criteria["tags.name"] = tag_name
    if node_id:
        criteria["node_path.id"] = node_id

    filter: dict[str, Any] = {}

    if criteria:
        filter.update(criteria)

    if pagination_cursor:
        cursor = PaginationCursor.load(pagination_cursor)
        filter["$or"] = [
            {"saved_at": {"$lt": cursor.date}},
            {"$and": [{"saved_at": {"$eq": cursor.date}}, {"_id": {"$lt": cursor.log_id}}]}
        ]

    results = db.logs.find(filter, _EXCLUDE_ATTACHMENT_DATA, sort=[("saved_at", -1), ("_id", -1)], limit=limit+1)
    logs = [Log(**log) async for log in results]

    # we previously fetched one extra log to check if there are more logs to fetch
    if len(logs) == limit + 1:
        # there is still more logs to fetch, so we need to return a next_cursor based on the last log WITHIN the
        # limit range
        next_cursor = PaginationCursor(logs[-2].saved_at, logs[-2].id).serialize()
        # remove the extra log
        logs.pop(-1)
    else:
        next_cursor = None

    return logs, next_cursor


async def _get_consolidated_data_aggregated_field(
        collection: AsyncIOMotorCollection, field_name: str, *,
        match=None,
        page=1, page_size=10
) -> tuple[list[str], PaginationInfo]:
    # Get all unique aggregated data field
    results = collection.aggregate(
        ([{"$match": match}] if match else []) +
        [
            {"$group": {"_id": "$" + field_name}},
            {"$sort": {"_id": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size}
        ]
    )
    values = [result["_id"] async for result in results]

    # Get the total number of unique aggregated field value
    results = collection.aggregate(
        ([{"$match": match}] if match else []) +
        [
            {"$group": {"_id": "$" + field_name}},
            {"$count": "total"}
        ]
    )
    total = (await results.next())["total"]

    return values, PaginationInfo.build(page=page, page_size=page_size, total=total)


async def _get_paginated_results(
        collection: AsyncIOMotorCollection, *,
        filter=None, projection=None, sort=None,
        page=1, page_size=10
) -> tuple[AsyncIOMotorCursor, PaginationInfo]:
    # Get results
    results = collection.find(
        filter=filter, projection=projection, sort=sort,
        skip=(page - 1) * page_size, limit=page_size
    )

    # Get the total number of results
    total = await collection.count_documents(filter or {})

    return results, PaginationInfo.build(page=page, page_size=page_size, total=total)


async def _get_consolidated_data_field(
        collection: AsyncIOMotorCollection, field_name: str, *, page=1, page_size=10
) -> tuple[list[str], PaginationInfo]:
    results, pagination = await _get_paginated_results(
        collection,
        projection=[field_name], sort={field_name: 1}, page=page, page_size=page_size
    )
    return [result[field_name] async for result in results], pagination


async def get_log_event_categories(db: Database, *, page=1, page_size=10) -> tuple[list[str], PaginationInfo]:
    return await _get_consolidated_data_aggregated_field(
        db.log_events, "category", page=page, page_size=page_size
    )


async def get_log_events(
        db: Database, *, event_category: str = None, page=1, page_size=10
) -> tuple[list[str], PaginationInfo]:
    return await _get_consolidated_data_aggregated_field(
        db.log_events, "name",
        page=page, page_size=page_size,
        match={"category": event_category} if event_category else None
    )


async def get_log_actor_types(db: Database, *, page=1, page_size=10) -> tuple[list[str], PaginationInfo]:
    return await _get_consolidated_data_field(db.log_actor_types, "type", page=page, page_size=page_size)


async def get_log_resource_types(db: Database, *, page=1, page_size=10) -> tuple[list[str], PaginationInfo]:
    return await _get_consolidated_data_field(db.log_resource_types, "type", page=page, page_size=page_size)


async def get_log_tag_categories(db: Database, *, page=1, page_size=10) -> tuple[list[str], PaginationInfo]:
    return await _get_consolidated_data_field(db.log_tag_categories, "category", page=page, page_size=page_size)


async def get_log_nodes(db: Database, *, parent_node_id=NotImplemented, page=1, page_size=10
                        ) -> tuple[list[Log.Node], PaginationInfo]:
    # please note that we use NotImplemented instead of None because None is a valid value for parent_node_id
    # (it means filtering on top nodes)
    if parent_node_id is NotImplemented:
        filter = {}
    else:
        filter = {"parent_node_id": parent_node_id}

    results, pagination = await _get_paginated_results(
        db.log_nodes,
        filter=filter,
        sort=[("name", 1)],
        page=page, page_size=page_size
    )
    return [Node(**result) async for result in results], pagination
