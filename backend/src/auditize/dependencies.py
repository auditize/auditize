from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database.dbm import get_dbm, open_db_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with open_db_session() as session:
        yield session
