import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database.dbm import SqlModel
from auditize.exceptions import UnknownModelException


async def save_sql_model(
    session: AsyncSession,
    model: SqlModel,
    *,
    constraint_rules: dict[str, Exception] | None = None,
) -> None:
    session.add(model)
    try:
        await session.commit()
    except IntegrityError as exc:
        if constraint_rules:
            for constraint_name, business_exc in constraint_rules.items():
                if constraint_name in str(exc):
                    raise business_exc
        raise
    await session.refresh(model)


async def update_sql_model[T: SqlModel](
    session: AsyncSession,
    model: T,
    update: BaseModel | dict,
    *,
    constraint_rules: dict[str, Exception] | None = None,
) -> None:
    if isinstance(update, BaseModel):
        update = update.model_dump(exclude_unset=True)
    for field, value in update.items():
        setattr(model, field, value)
    await save_sql_model(session, model, constraint_rules=constraint_rules)


async def get_sql_model[T: SqlModel](
    session: AsyncSession, model_class: type[T], lookup: uuid.UUID | Any
) -> T:
    if isinstance(lookup, uuid.UUID):
        lookup = model_class.id == lookup
    model = await session.scalar(select(model_class).where(lookup))
    if not model:
        raise UnknownModelException()
    return model


async def delete_sql_model[T: SqlModel](
    session: AsyncSession, model_class: type[T], lookup: uuid.UUID | Any
) -> None:
    if isinstance(lookup, uuid.UUID):
        lookup = model_class.id == lookup
    result = await session.execute(delete(model_class).where(lookup))
    await session.commit()
    if result.rowcount == 0:
        raise UnknownModelException()
