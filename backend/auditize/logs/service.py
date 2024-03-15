from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorCollection
from aiocache import Cache
from icecream import ic

from auditize.logs.models import Log
from auditize.common.mongo import Database


cache = Cache(Cache.MEMORY)


async def _store_unique_data(collection: AsyncIOMotorCollection, data: dict[str, str]):
    cache_key = "%s:%s" % (collection.name, ":".join(val or "" for val in data.values()))
    if await cache.exists(cache_key):
        return
    ic(f"storing {collection.name!r} {data!r}")
    await collection.update_one(data, {"$set": {}}, upsert=True)
    await cache.set(cache_key, True)


async def save_log(db: Database, log: Log) -> ObjectId:
    result = await db.logs.insert_one(log.model_dump(exclude={"id"}))

    await _store_unique_data(
        db.log_events, {"category": log.event.category, "name": log.event.name}
    )

    for key in log.source:
        await _store_unique_data(db.log_source_keys, {"key": key})

    if log.actor:
        await _store_unique_data(db.log_actor_types, {"type": log.actor.type})
        for extra_key in log.actor.extra:
            await _store_unique_data(
                db.log_actor_extra_keys, {"key": extra_key}
            )

    if log.resource:
        await _store_unique_data(db.log_resource_types, {"type": log.resource.type})
        for extra_key in log.resource.extra:
            await _store_unique_data(
                db.log_resource_extra_keys, {"key": extra_key}
            )

    for level1_key, sub_keys in log.details.items():
        for level2_key in sub_keys:
            await _store_unique_data(
                db.log_detail_keys, {"level1_key": level1_key, "level2_key": level2_key}
            )

    for tag in log.tags:
        if tag.category:
            await _store_unique_data(db.log_tag_categories, {"category": tag.category})

    parent_node_id = None
    for node in log.node_path:
        await _store_unique_data(db.log_nodes, {
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
    data = await db.logs.find_one(
        ObjectId(log_id),
        # exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
        {"attachments.data": 0},
    )
    return Log(**data)


async def get_log_attachment(db: Database, log_id: ObjectId | str, attachment_idx: int) -> Log.Attachment:
    result = await db.logs.find_one(
        {"_id": ObjectId(log_id)},
        {"attachments": {"$slice": [attachment_idx, 1]}},
    )
    return Log.Attachment(**result["attachments"][0])
