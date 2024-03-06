from datetime import datetime
from bson.objectid import ObjectId
from typing import Annotated

from fastapi import FastAPI
from pydantic import BaseModel, Field, BeforeValidator
import motor.motor_asyncio


mongo = motor.motor_asyncio.AsyncIOMotorClient()
db = mongo.get_database("auditize")
log_collection = db.get_collection("logs")


PyObjectId = Annotated[str, BeforeValidator(str)]


class Event(BaseModel):
    name: str = Field(...)
    category: str


class LogBase(BaseModel):
    event: Event
    occurred_at: datetime


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
