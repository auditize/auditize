import re
from datetime import datetime
from bson.objectid import ObjectId
from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field, BeforeValidator
import motor.motor_asyncio


DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def validate_datetime(value):
    if isinstance(value, str) and not DATETIME_PATTERN.match(value):
        raise ValueError(f'invalid datetime format, expected "{DATETIME_PATTERN.pattern}", got "{value}"')
    return value


mongo = motor.motor_asyncio.AsyncIOMotorClient()
db = mongo.get_database("auditize")
log_collection = db.get_collection("logs")


PyObjectId = Annotated[str, BeforeValidator(str)]

AuditizeDatetime = Annotated[datetime, BeforeValidator(validate_datetime)]


class Event(BaseModel):
    name: str = Field(...)
    category: str


class LogBase(BaseModel):
    event: Event
    occurred_at: AuditizeDatetime


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
