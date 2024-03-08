from typing import Optional
import re
from datetime import datetime, timezone
from bson.objectid import ObjectId
from typing import Annotated

from fastapi import FastAPI
from pydantic import ConfigDict, BaseModel, Field, BeforeValidator
import motor.motor_asyncio
from motor import MotorCollection
from icecream import ic
from aiocache import Cache

ic.configureOutput(includeContext=True)

DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def validate_datetime(value):
    """
    Validate datetime string in ISO 8601 format ("YYYY-MM-DDTHH:MM:SS.sssZ" to be specific).
    """
    if isinstance(value, str) and not DATETIME_PATTERN.match(value):
        raise ValueError(f'invalid datetime format, expected "{DATETIME_PATTERN.pattern}", got "{value}"')
    return value


def serialize_datetime(dt: datetime) -> str:
    """
    Serialize a datetime object to a string in ISO 8601 format ("YYYY-MM-DDTHH:MM:SS.sssZ" to be specific).
    """
    # first, make sure we're dealing with an appropriate UTC datetime:
    dt = dt.astimezone(timezone.utc)
    # second, remove timezone info so that isoformat() won't indicate "+00:00":
    dt = dt.replace(tzinfo=None)
    # third, format:
    return dt.isoformat(timespec="milliseconds") + "Z"


mongo = motor.motor_asyncio.AsyncIOMotorClient()
db = mongo.get_database("auditize")
log_collection = db.get_collection("logs")
cache = Cache(Cache.MEMORY)


class Log(BaseModel):
    class Event(BaseModel):
        name: str
        category: str

    class Actor(BaseModel):
        type: str
        id: str
        name: str

    class Resource(BaseModel):
        type: str
        id: str
        name: str

    id: Optional[ObjectId] = Field(default=None, validation_alias="_id")
    event: Event
    occurred_at: datetime
    saved_at: datetime = Field(default_factory=datetime.utcnow)
    source: dict[str, str] = Field(default_factory=dict)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Actor] = Field(default=None)
    context: dict[str, dict[str, str]] = Field(default_factory=dict)

    model_config = ConfigDict(
        arbitrary_types_allowed=True
    )


class _LogBase(BaseModel):
    class Event(BaseModel):
        name: str
        category: str

    class Actor(BaseModel):
        type: str
        id: str
        name: str

    class Resource(BaseModel):
        type: str
        id: str
        name: str

    event: Event
    occurred_at: Annotated[datetime, BeforeValidator(validate_datetime)]
    source: dict[str, str] = Field(default_factory=dict)
    actor: Optional[Actor] = Field(default=None)
    resource: Optional[Resource] = Field(default=None)
    context: dict[str, dict[str, str]] = Field(default_factory=dict)


class LogCreationRequest(_LogBase):
    def to_log(self) -> Log:
        return Log.model_validate(self.model_dump())


class LogCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)]


class _LogReadingResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)]
    saved_at: datetime


class LogReadingResponse(_LogBase, _LogReadingResponse):
    model_config = ConfigDict(
        json_encoders={datetime: serialize_datetime}
    )

    @classmethod
    def from_log(cls, log: Log):
        return cls.model_validate(log.model_dump())


async def store_unique_data(collection: MotorCollection, data: dict[str, str]):
    cache_key = "%s:%s" % (collection.name, ":".join(data.values()))
    if await cache.exists(cache_key):
        return
    ic(f"storing {collection.name!r} {data!r}")
    await collection.update_one(data, {"$set": {}}, upsert=True)
    await cache.set(cache_key, True)


async def save_log(log: Log) -> ObjectId:
    result = await log_collection.insert_one(log.model_dump())
    await store_unique_data(
        db.get_collection("events"), {"category": log.event.category, "name": log.event.name}
    )
    for key in log.source:
        await store_unique_data(db.get_collection("source_keys"), {"key": key})
    if log.actor:
        await store_unique_data(db.get_collection("actor_types"), {"type": log.actor.type})
    if log.resource:
        await store_unique_data(db.get_collection("resource_types"), {"type": log.resource.type})
    for level1_key, sub_keys in log.context.items():
        for level2_key in sub_keys:
            await store_unique_data(
                db.get_collection("context_keys"), {"level1_key": level1_key, "level2_key": level2_key}
            )
    return result.inserted_id


async def get_log(log_id: ObjectId | str) -> Log:
    data = await log_collection.find_one(ObjectId(log_id))
    return Log(**data)


app = FastAPI()


@app.post("/logs", status_code=201)
async def create_log(log_req: LogCreationRequest) -> LogCreationResponse:
    log_id = await save_log(log_req.to_log())
    return LogCreationResponse(id=log_id)


@app.get("/logs/{log_id}")
async def read_log(log_id: str) -> LogReadingResponse:
    log = await get_log(log_id)
    return LogReadingResponse.from_log(log)
