from contextlib import asynccontextmanager
from datetime import timezone
from functools import lru_cache

from bson.binary import UuidRepresentation
from bson.codec_options import CodecOptions
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorClientSession,
    AsyncIOMotorCollection,
)


class Collection:
    def __init__(self, name):
        self.name = name

    @lru_cache
    def __get__(self, db: "Database", _) -> AsyncIOMotorCollection:
        return db.db.get_collection(
            self.name,
            codec_options=CodecOptions(
                tz_aware=True,
                tzinfo=timezone.utc,
                uuid_representation=UuidRepresentation.STANDARD,
            ),
        )


class Database:
    def __init__(self, name: str, client: AsyncIOMotorClient):
        self.name = name
        self.client = client

    @property
    def db(self):
        return self.client.get_database(self.name)

    def get_collection(self, name):
        return self.db.get_collection(name)

    @asynccontextmanager
    async def transaction(self) -> AsyncIOMotorClientSession:
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                yield session

    async def ping(self):
        await self.client.server_info()
