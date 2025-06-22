from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database.dbm import Base
from auditize.resource.pagination.page.models import PagePaginationInfo


async def find_paginated_by_page[T: Base](
    session: AsyncSession,
    model_class: type[T],
    *,
    filter=None,
    order_by=None,
    page=1,
    page_size=10,
) -> tuple[list[T], PagePaginationInfo]:
    # Get results
    query = select(model_class)
    if filter is not None:
        query = query.where(filter)
    if order_by is not None:
        query = query.order_by(order_by)
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
