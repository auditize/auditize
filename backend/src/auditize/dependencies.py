from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database.dbm import open_db_session


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with open_db_session() as session:
        yield session
