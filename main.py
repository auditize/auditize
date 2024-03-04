from datetime import datetime

from fastapi import FastAPI
from pydantic import BaseModel, Field
import motor.motor_asyncio


mongo = motor.motor_asyncio.AsyncIOMotorClient()
db = mongo.get_database("auditize")
log_collection = db.get_collection("logs")


class Event(BaseModel):
    name: str = Field(...)
    category: str


class LogBase(BaseModel):
    event: Event
    occurred_at: datetime


app = FastAPI()


@app.post("/logs")
async def create_log(log: LogBase):
    result = await log_collection.insert_one(log.model_dump())
    return {"id": str(result.inserted_id)}
