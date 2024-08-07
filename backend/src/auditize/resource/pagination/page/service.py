from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor

from auditize.resource.pagination.page.models import PagePaginationInfo


async def find_paginated_by_page(
    collection: AsyncIOMotorCollection,
    *,
    filter=None,
    projection=None,
    sort=None,
    page=1,
    page_size=10,
) -> tuple[AsyncIOMotorCursor, PagePaginationInfo]:
    # Get results
    results = collection.find(
        filter=filter,
        projection=projection,
        sort=sort,
        skip=(page - 1) * page_size,
        limit=page_size,
    )

    # Get the total number of results
    total = await collection.count_documents(filter or {})

    return results, PagePaginationInfo.build(
        page=page, page_size=page_size, total=total
    )
