from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, Form, Response, Path, Depends, HTTPException
from pydantic import Field, BeforeValidator

from auditize.logs.api_models import (
    LogCreationRequest, LogCreationResponse, LogReadingResponse, LogsReadingResponse,
    LogEventCategoryListResponse, LogEventNameListResponse, LogActorTypeListResponse, LogResourceTypeListResponse,
    LogTagCategoryListResponse, LogNodeListResponse, LogNodeResponse,
    PagePaginationParams
)
from auditize.logs import service
from auditize.common.mongo import Database, get_db
from auditize.common.api import COMMON_RESPONSES
from auditize.common.utils import validate_datetime

router = APIRouter()


async def handle_paginated_data_request(
        db: Database, response_class, service_func, page_params: PagePaginationParams, **kwargs
):
    items, pagination = await service_func(
        db, page=page_params.page, page_size=page_params.page_size, **kwargs
    )
    return response_class.build(items, pagination)


@router.get(
    "/logs/events",
    summary="Get log event names",
    operation_id="get_log_event_names",
    tags=["logs"]
)
async def get_log_event_names(
        db: Annotated[Database, Depends(get_db)],
        page_params: Annotated[PagePaginationParams, Depends()], category: str = None
) -> LogEventNameListResponse:
    return await handle_paginated_data_request(
        db, LogEventNameListResponse, service.get_log_events, page_params, event_category=category
    )


@router.get(
    "/logs/event-categories",
    summary="Get log event categories",
    operation_id="get_log_event_categories",
    tags=["logs"]
)
async def get_log_event_categories(
        db: Annotated[Database, Depends(get_db)], page_params: Annotated[PagePaginationParams, Depends()]
) -> LogEventCategoryListResponse:
    items, pagination = await service.get_log_event_categories(db, page=page_params.page, page_size=page_params.page_size)
    return LogEventCategoryListResponse.build(items, pagination)


@router.get(
    "/logs/actor-types",
    summary="Get log actor types",
    operation_id="get_log_actor_types",
    tags=["logs"]
)
async def get_log_actor_types(
        db: Annotated[Database, Depends(get_db)], page_params: Annotated[PagePaginationParams, Depends()]
) -> LogActorTypeListResponse:
    return await handle_paginated_data_request(
        db, LogActorTypeListResponse, service.get_log_actor_types, page_params
    )


@router.get(
    "/logs/resource-types",
    summary="Get log resource types",
    operation_id="get_log_resource_types",
    tags=["logs"]
)
async def get_log_resource_types(
        db: Annotated[Database, Depends(get_db)], page_params: Annotated[PagePaginationParams, Depends()]
) -> LogResourceTypeListResponse:
    return await handle_paginated_data_request(
        db, LogResourceTypeListResponse, service.get_log_resource_types, page_params
    )


@router.get(
    "/logs/tag-categories",
    summary="Get log tag categories",
    operation_id="get_log_tag_categories",
    tags=["logs"]
)
async def get_log_tag_categories(
        db: Annotated[Database, Depends(get_db)], page_params: Annotated[PagePaginationParams, Depends()]
) -> LogTagCategoryListResponse:
    return await handle_paginated_data_request(
        db, LogTagCategoryListResponse, service.get_log_tag_categories, page_params
    )


@router.get(
    "/logs/nodes",
    summary="Get log nodes",
    operation_id="get_log_nodes",
    tags=["logs"]
)
async def get_log_nodes(
    db: Annotated[Database, Depends(get_db)],
    root: bool = False,
    parent_node_id: str = None,
    page_params: Annotated[PagePaginationParams, Depends()] = PagePaginationParams()
) -> LogNodeListResponse:
    if root and parent_node_id is not None:
        raise HTTPException(400, "Parameters 'root' and 'parent_node_id' are mutually exclusive.")

    if root:
        filter_args = {"parent_node_id": None}
    elif parent_node_id:
        filter_args = {"parent_node_id": parent_node_id}
    else:
        filter_args = {}

    return await handle_paginated_data_request(
        db, LogNodeListResponse, service.get_log_nodes, page_params, **filter_args
    )


@router.get(
    "/logs/nodes/{node_id}",
    summary="Get a log node",
    operation_id="get_log_node",
    tags=["logs"]
)
async def get_log_node(
    db: Annotated[Database, Depends(get_db)],
    node_id: Annotated[str, Path(title="Node ID")]
):
    node = await service.get_log_node(db, node_id)
    return LogNodeResponse.from_node(node)


@router.post(
    "/logs",
    status_code=201,
    summary="Create a log",
    operation_id="create_log",
    tags=["logs"]
)
async def create_log(db: Annotated[Database, Depends(get_db)], log_req: LogCreationRequest) -> LogCreationResponse:
    log_id = await service.save_log(db, log_req.to_log())
    return LogCreationResponse(id=log_id)


@router.post(
    "/logs/{log_id}/attachments",
    status_code=204,
    response_class=Response,
    summary="Add a file attachment to a log",
    operation_id="add_log_attachment",
    tags=["logs"]
)
async def add_attachment(
        db: Annotated[Database, Depends(get_db)],
        log_id: Annotated[str, Path(
            title="Log ID",
            description="The ID of the log to attach the file to"
        )],
        file: UploadFile,
        type: Annotated[str, Form(
            title="Attachment type",
            description="The 'functional' type of the attachment",
            json_schema_extra={"example": "Configuration file"}
        )],
        name: Annotated[str, Form(
            title="Attachment name",
            description="The name of the attachment. If not provided, the name of the uploaded file will be used.",
            json_schema_extra={
                "nullable": True,
                "example": "config.json"
            },
        )] = None,
        mime_type: Annotated[str, Form(
            title="Attachment MIME type",
            description="The MIME type of the attachment. If not provided, the MIME type of the uploaded "
                        "file will be used.",
            json_schema_extra={
                "nullable": True,
                "example": "application/json"
            }
        )] = None
) -> None:
    await service.save_log_attachment(
        db,
        log_id,
        name or file.filename,
        type,
        mime_type or file.content_type,
        await file.read()
    )


@router.get(
    "/logs/{log_id}",
    summary="Get a log",
    operation_id="get_log",
    tags=["logs"],
    responses=COMMON_RESPONSES
)
async def get_log(
        db: Annotated[Database, Depends(get_db)], log_id: Annotated[str, Path(title="Log ID")]) -> LogReadingResponse:
    log = await service.get_log(db, log_id)
    return LogReadingResponse.from_log(log)


@router.get(
    "/logs/{log_id}/attachments/{attachment_idx}",
    summary="Download a log attachment",
    operation_id="get_log_attachment",
    tags=["logs"]
)
async def get_log_attachment(
        db: Annotated[Database, Depends(get_db)],
        log_id: str = Path(title="Log ID"),
        attachment_idx: int = Path(
            title="Attachment index",
            description="The index of the attachment in the log's attachments list (starts from 0)"
        )
):
    attachment = await service.get_log_attachment(db, log_id, attachment_idx)
    return Response(
        content=attachment.data,
        media_type=attachment.mime_type,
        headers={"Content-Disposition": f"attachment; filename={attachment.name}"}
    )


@router.get(
    "/logs",
    summary="Get logs",
    operation_id="get_logs",
    tags=["logs"]
)
async def get_logs(
        db: Annotated[Database, Depends(get_db)],
        event_name: str = None,
        event_category: str = None,
        actor_type: str = None, actor_name: str = None,
        resource_type: str = None, resource_name: str = None,
        tag_category: str = None, tag_name: str = None, tag_id: str = None,
        node_id: str = None,
        since: Annotated[Optional[datetime], BeforeValidator(validate_datetime)] = None,
        until: Annotated[Optional[datetime], BeforeValidator(validate_datetime)] = None,
        limit: int = 10,
        cursor: str = None
) -> LogsReadingResponse:
    # FIXME: we must check that "until" is greater than "since"
    logs, next_cursor = await service.get_logs(
        db,
        event_name=event_name, event_category=event_category,
        actor_type=actor_type, actor_name=actor_name,
        resource_type=resource_type, resource_name=resource_name,
        tag_category=tag_category, tag_name=tag_name, tag_id=tag_id,
        node_id=node_id,
        since=since, until=until,
        limit=limit, pagination_cursor=cursor
    )
    return LogsReadingResponse.from_logs(logs, next_cursor)
