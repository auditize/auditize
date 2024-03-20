from bson import ObjectId

from auditize.logs.models import Log
from auditize.common.mongo import Database
from auditize.common.exceptions import UnknownModelException


# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}


async def save_log(db: Database, log: Log) -> ObjectId:
    result = await db.logs.insert_one(log.model_dump(exclude={"id"}))

    await db.store_unique_data(
        db.log_events, {"category": log.event.category, "name": log.event.name}
    )

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
    return Log.Attachment(**result["attachments"][0])


async def get_logs(db: Database, limit: int = 10) -> list[Log]:
    cursor = db.logs.find({}, _EXCLUDE_ATTACHMENT_DATA, sort=[("saved_at", -1)], limit=limit)
    return [Log(**log) async for log in cursor]
