#!/usr/bin/env python

import asyncio
import os

from motor.motor_asyncio import AsyncIOMotorClient


async def cleanup_db(db_name: str):
    client = AsyncIOMotorClient()
    db = client.get_database(db_name)
    for collection_name in await db.list_collection_names():
        await db[collection_name].delete_many({})


if __name__ == "__main__":
    asyncio.run(cleanup_db("auditize_logs_" + os.environ["AUDITIZE_REPO"]))
