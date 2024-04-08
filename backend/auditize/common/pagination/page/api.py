from auditize.common.mongo import Database
from auditize.common.pagination.page.api_models import PagePaginationParams


async def handle_page_paginated_request(
        db: Database, response_class, service_func, page_params: PagePaginationParams,
        **service_func_kwargs
):
    items, pagination = await service_func(
        db, page=page_params.page, page_size=page_params.page_size, **service_func_kwargs
    )
    return response_class.build(items, pagination)
