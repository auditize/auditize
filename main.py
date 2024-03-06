import re
from datetime import datetime, timezone
from bson.objectid import ObjectId
from typing import Annotated

from fastapi import FastAPI
from pydantic import ConfigDict, BaseModel, Field, BeforeValidator
import motor.motor_asyncio


DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def validate_datetime(value):
    """
    Validate datetime string in ISO 8601 format (("YYYY-MM-DDTHH:MM:SS.sssZ" to be specific).
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


PyObjectId = Annotated[str, BeforeValidator(str)]


class Event(BaseModel):
    name: str = Field(...)
    category: str


class LogBase(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: serialize_datetime}
    )

    event: Event
    occurred_at: Annotated[datetime, BeforeValidator(validate_datetime)]


class Log(LogBase):
    id: PyObjectId = Field(validation_alias="_id")


class LogCreation(LogBase):
    pass


class LogCreated(BaseModel):
    id: str


async def save_log(log: LogCreation) -> str:
    result = await log_collection.insert_one({
        **log.model_dump(),
        "created_at": datetime.utcnow(),
    })
    return str(result.inserted_id)


async def get_log(log_id: str) -> Log:
    data = await log_collection.find_one(ObjectId(log_id))
    return Log(**data)


app = FastAPI()


@app.post("/logs", status_code=201)
async def create_log(log: LogCreation) -> LogCreated:
    log_id = await save_log(log)
    return LogCreated(id=log_id)


@app.get("/logs/{log_id}")
async def read_log(log_id: str) -> Log:
    log = await get_log(log_id)
    return log
