import uuid
from typing import Any

from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.models.page_pagination import PagePaginationInfo
from auditize.database.sql.models import SqlModel
from auditize.exceptions import NotFoundError


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
        raise NotFoundError()
    return model


async def delete_sql_model[T: SqlModel](
    session: AsyncSession, model_class: type[T], lookup: uuid.UUID | Any
) -> None:
    if isinstance(lookup, uuid.UUID):
        lookup = model_class.id == lookup
    result = await session.execute(delete(model_class).where(lookup))
    await session.commit()
    if result.rowcount == 0:
        raise NotFoundError()


async def find_paginated_by_page[T: SqlModel](
    session: AsyncSession,
    model_class: type[T],
    *,
    filter=None,
    order_by: list | tuple | None | Any = None,
    page=1,
    page_size=10,
) -> tuple[list[T], PagePaginationInfo]:
    # Get results
    query = select(model_class)
    if filter is not None:
        query = query.where(filter)
    if order_by is not None:
        query = query.order_by(
            *(order_by if isinstance(order_by, (list, tuple)) else [order_by])
        )
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await session.execute(query)
    models = list(result.scalars().all())

    # Get the total number of results
    count_query = select(func.count()).select_from(model_class)
    if filter is not None:
        count_query = count_query.where(filter)
    total_result = await session.execute(count_query)
    total = total_result.scalar()

    return models, PagePaginationInfo.build(page=page, page_size=page_size, total=total)
