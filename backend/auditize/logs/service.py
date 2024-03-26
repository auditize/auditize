from datetime import datetime
import base64
import binascii

import bson.errors
from bson import ObjectId
import json

from pydantic import BaseModel, field_validator, field_serializer
from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.logs.models import Log, PaginationInfo
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


async def store_log_event(db: Database, event: Log.Event):
    await db.store_unique_data(
        db.log_events, {"category": event.category, "name": event.name}
    )


async def save_log(db: Database, log: Log) -> ObjectId:
    result = await db.logs.insert_one(log.model_dump(exclude={"id"}))

    await store_log_event(db, log.event)

    for key in log.source:
        await db.store_unique_data(db.log_source_keys, {"key": key})

    if log.actor:
        await db.store_unique_data(db.log_actor_types, {"type": log.actor.type})
        for extra_key in log.actor.extra:
            await db.store_unique_data(
                db.log_actor_extra_keys, {"key": extra_key}
            )

    if log.resource:
        await db.store_unique_data(db.log_resource_types, {"type": log.resource.type})
        for extra_key in log.resource.extra:
            await db.store_unique_data(
                db.log_resource_extra_keys, {"key": extra_key}
            )

    for level1_key, sub_keys in log.details.items():
        for level2_key in sub_keys:
            await db.store_unique_data(
                db.log_detail_keys, {"level1_key": level1_key, "level2_key": level2_key}
            )

    for tag in log.tags:
        if tag.category:
            await db.store_unique_data(db.log_tag_categories, {"category": tag.category})

    parent_node_id = None
    for node in log.node_path:
        await db.store_unique_data(db.log_nodes, {
            "parent_node_id": parent_node_id, "id": node.id, "name": node.name
        })
        parent_node_id = node.id

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


async def get_logs(db: Database, limit: int = 10, pagination_cursor: str = None) -> tuple[list[Log], str | None]:
    if pagination_cursor:
        cursor = PaginationCursor.load(pagination_cursor)
        filter = {
            "$or": [
                {"saved_at": {"$lt": cursor.date}},
                {"$and": [{"saved_at": {"$eq": cursor.date}}, {"_id": {"$lt": cursor.log_id}}]}
            ]
        }
    else:
        filter = None

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


async def _get_consolidated_data_aggregated(
        collection: AsyncIOMotorCollection, field_name: str, *,
        match=None,
        page=1, page_size=10
) -> tuple[list[str], PaginationInfo]:
    # Get all unique aggregated data field
    results = collection.aggregate(
        ([{"$match": match}] if match else []) +
        [
            {"$group": {"_id": field_name}},
            {"$sort": {"_id": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size}
        ]
    )
    categories = [result["_id"] async for result in results]

    # Get the total number of unique aggregated field value
    results = collection.aggregate(
        ([{"$match": match}] if match else []) +
        [
            {"$group": {"_id": field_name}},
            {"$count": "total"}
        ]
    )
    total = (await results.next())["total"]

    return categories, PaginationInfo.build(page=page, page_size=page_size, total=total)


async def get_log_event_categories(db: Database, *, page=1, page_size=10) -> tuple[list[str], PaginationInfo]:
    return await _get_consolidated_data_aggregated(
        db.log_events, "$category", page=page, page_size=page_size
    )


async def get_log_events(
        db: Database, *, event_category: str = None, page=1, page_size=10
) -> tuple[list[str], PaginationInfo]:
    return await _get_consolidated_data_aggregated(
        db.log_events, "$name",
        page=page, page_size=page_size,
        match={"category": event_category} if event_category else None
    )
