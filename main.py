from typing import Optional
import re
from datetime import datetime, timezone
from bson.objectid import ObjectId
from typing import Annotated

from fastapi import FastAPI
from pydantic import ConfigDict, BaseModel, Field, BeforeValidator
import motor.motor_asyncio
from icecream import ic


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


class Event(BaseModel):
    name: str
    category: str


class Log(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    id: Optional[ObjectId] = Field(default=None, validation_alias="_id")
    event: Event
    occurred_at: datetime
    saved_at: datetime = Field(default_factory=datetime.utcnow)


class LogCreationRequest(BaseModel):
    event: Event
    occurred_at: Annotated[datetime, BeforeValidator(validate_datetime)]

    def to_log(self) -> Log:
        return Log.model_validate(self.dict())


class LogCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)]


class LogReadingResponse(BaseModel):
    model_config = ConfigDict(
        json_encoders={datetime: serialize_datetime}
    )

    id: Annotated[str, BeforeValidator(str)]
    event: Event
    occurred_at: datetime
    saved_at: datetime

    @classmethod
    def from_log(cls, log: Log):
        return cls.model_validate(log.dict())


async def save_log(log: Log) -> ObjectId:
    result = await log_collection.insert_one(log.model_dump())
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
