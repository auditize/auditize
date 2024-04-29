from typing import Annotated, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, Form, Response, Path, Depends, HTTPException
from pydantic import BeforeValidator

from auditize.logs.api_models import (
    LogCreationRequest, LogCreationResponse, LogReadingResponse, LogsReadingResponse,
    LogEventCategoryListResponse, LogEventNameListResponse, LogActorTypeListResponse, LogResourceTypeListResponse,
    LogTagCategoryListResponse, LogNodeListResponse, LogNodeResponse
)
from auditize.logs import service
from auditize.common.db import DatabaseManager, get_dbm
from auditize.common.api import COMMON_RESPONSES
from auditize.common.utils import validate_datetime
from auditize.common.pagination.page.api_models import PagePaginationParams
from auditize.auth import Authenticated, get_authenticated

router = APIRouter()


@router.get(
    "/repos/{repo_id}/logs/events",
    summary="Get log event names",
    operation_id="get_log_event_names",
    tags=["logs"]
)
async def get_log_event_names(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()], category: str = None
) -> LogEventNameListResponse:
    events, pagination = await service.get_log_events(
        dbm, repo_id, event_category=category, page=page_params.page, page_size=page_params.page_size,
    )
    return LogEventNameListResponse.build(events, pagination)


@router.get(
    "/repos/{repo_id}/logs/event-categories",
    summary="Get log event categories",
    operation_id="get_log_event_categories",
    tags=["logs"]
)
async def get_log_event_categories(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()]
) -> LogEventCategoryListResponse:
    categories, pagination = await service.get_log_event_categories(
        dbm, repo_id,
        page=page_params.page, page_size=page_params.page_size
    )
    return LogEventCategoryListResponse.build(categories, pagination)


@router.get(
    "/repos/{repo_id}/logs/actor-types",
    summary="Get log actor types",
    operation_id="get_log_actor_types",
    tags=["logs"]
)
async def get_log_actor_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()]
) -> LogActorTypeListResponse:
    actor_types, pagination = await service.get_log_actor_types(
        dbm, repo_id, page=page_params.page, page_size=page_params.page_size
    )
    return LogActorTypeListResponse.build(actor_types, pagination)


@router.get(
    "/repos/{repo_id}/logs/resource-types",
    summary="Get log resource types",
    operation_id="get_log_resource_types",
    tags=["logs"]
)
async def get_log_resource_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()]
) -> LogResourceTypeListResponse:
    resource_types, pagination = await service.get_log_resource_types(
        dbm, repo_id, page=page_params.page, page_size=page_params.page_size
    )
    return LogResourceTypeListResponse.build(resource_types, pagination)


@router.get(
    "/repos/{repo_id}/logs/tag-categories",
    summary="Get log tag categories",
    operation_id="get_log_tag_categories",
    tags=["logs"]
)
async def get_log_tag_categories(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()]
) -> LogTagCategoryListResponse:
    tag_categories, pagination = await service.get_log_tag_categories(
        dbm, repo_id, page=page_params.page, page_size=page_params.page_size
    )
    return LogTagCategoryListResponse.build(tag_categories, pagination)


@router.get(
    "/repos/{repo_id}/logs/nodes",
    summary="Get log nodes",
    operation_id="get_log_nodes",
    tags=["logs"]
)
async def get_log_nodes(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
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

    nodes, pagination = await service.get_log_nodes(
        dbm, repo_id, page=page_params.page, page_size=page_params.page_size, **filter_args
    )
    return LogNodeListResponse.build(nodes, pagination)


@router.get(
    "/repos/{repo_id}/logs/nodes/{node_id}",
    summary="Get a log node",
    operation_id="get_log_node",
    tags=["logs"]
)
async def get_log_node(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    node_id: Annotated[str, Path(title="Node ID")]
):
    node = await service.get_log_node(dbm, repo_id, node_id)
    return LogNodeResponse.from_node(node)


@router.post(
    "/repos/{repo_id}/logs",
    status_code=201,
    summary="Create a log",
    operation_id="create_log",
    tags=["logs"]
)
async def create_log(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    log_req: LogCreationRequest
) -> LogCreationResponse:
    log_id = await service.save_log(dbm, repo_id, log_req.to_log())
    return LogCreationResponse(id=log_id)


@router.post(
    "/repos/{repo_id}/logs/{log_id}/attachments",
    status_code=204,
    response_class=Response,
    summary="Add a file attachment to a log",
    operation_id="add_log_attachment",
    tags=["logs"]
)
async def add_attachment(
        dbm: Annotated[DatabaseManager, Depends(get_dbm)],
        authenticated: Annotated[Authenticated, Depends(get_authenticated)],
        repo_id: str,
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
        dbm,
        repo_id,
        log_id,
        name or file.filename,
        type,
        mime_type or file.content_type,
        await file.read()
    )


@router.get(
    "/repos/{repo_id}/logs/{log_id}",
    summary="Get a log",
    operation_id="get_log",
    tags=["logs"],
    responses=COMMON_RESPONSES
)
async def get_log(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    log_id: Annotated[str, Path(title="Log ID")]
) -> LogReadingResponse:
    log = await service.get_log(dbm, repo_id, log_id)
    return LogReadingResponse.from_log(log)


@router.get(
    "/repos/{repo_id}/logs/{log_id}/attachments/{attachment_idx}",
    summary="Download a log attachment",
    operation_id="get_log_attachment",
    tags=["logs"]
)
async def get_log_attachment(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    repo_id: str,
    log_id: str = Path(title="Log ID"),
    attachment_idx: int = Path(
        title="Attachment index",
        description="The index of the attachment in the log's attachments list (starts from 0)"
    )
):
    attachment = await service.get_log_attachment(dbm, repo_id, log_id, attachment_idx)
    return Response(
        content=attachment.data,
        media_type=attachment.mime_type,
        headers={"Content-Disposition": f"attachment; filename={attachment.name}"}
    )


@router.get(
    "/repos/{repo_id}/logs",
    summary="Get logs",
    operation_id="get_logs",
    tags=["logs"]
)
async def get_logs(
        dbm: Annotated[DatabaseManager, Depends(get_dbm)],
        authenticated: Annotated[Authenticated, Depends(get_authenticated)],
        repo_id: str,
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
        dbm,
        repo_id,
        event_name=event_name, event_category=event_category,
        actor_type=actor_type, actor_name=actor_name,
        resource_type=resource_type, resource_name=resource_name,
        tag_category=tag_category, tag_name=tag_name, tag_id=tag_id,
        node_id=node_id,
        since=since, until=until,
        limit=limit, pagination_cursor=cursor
    )
    return LogsReadingResponse.build(logs, next_cursor)
