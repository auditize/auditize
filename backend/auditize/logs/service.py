from bson import ObjectId

from motor import motor_asyncio, MotorCollection
from aiocache import Cache
from icecream import ic

from auditize.logs.models import Log


mongo = motor_asyncio.AsyncIOMotorClient()
db = mongo.get_database("auditize")
log_collection = db.get_collection("logs")
cache = Cache(Cache.MEMORY)


async def _store_unique_data(collection: MotorCollection, data: dict[str, str]):
    cache_key = "%s:%s" % (collection.name, ":".join(data.values()))
    if await cache.exists(cache_key):
        return
    ic(f"storing {collection.name!r} {data!r}")
    await collection.update_one(data, {"$set": {}}, upsert=True)
    await cache.set(cache_key, True)


async def save_log(log: Log) -> ObjectId:
    result = await log_collection.insert_one(log.model_dump())
    await _store_unique_data(
        db.get_collection("events"), {"category": log.event.category, "name": log.event.name}
    )
    for key in log.source:
        await _store_unique_data(db.get_collection("source_keys"), {"key": key})
    if log.actor:
        await _store_unique_data(db.get_collection("actor_types"), {"type": log.actor.type})
    if log.resource:
        await _store_unique_data(db.get_collection("resource_types"), {"type": log.resource.type})
    for level1_key, sub_keys in log.context.items():
        for level2_key in sub_keys:
            await _store_unique_data(
                db.get_collection("context_keys"), {"level1_key": level1_key, "level2_key": level2_key}
            )
    return result.inserted_id


async def get_log(log_id: ObjectId | str) -> Log:
    data = await log_collection.find_one(ObjectId(log_id))
    return Log(**data)