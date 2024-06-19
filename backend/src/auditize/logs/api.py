from typing import Annotated

from fastapi import APIRouter, Depends, Form, Path, Response, UploadFile

from auditize.auth.authorizer import (
    AuthorizedOnLogsRead,
    AuthorizedOnLogsWrite,
)
from auditize.config import get_config
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import PayloadTooLarge, ValidationError
from auditize.helpers.api.errors import error_responses
from auditize.helpers.api.validators import (
    IDENTIFIER_PATTERN_STRING,
)
from auditize.helpers.pagination.cursor.api_models import CursorPaginationParams
from auditize.helpers.pagination.page.api_models import PagePaginationParams
from auditize.logs import service
from auditize.logs.api_models import (
    LogCreationRequest,
    LogCreationResponse,
    LogNodeListResponse,
    LogNodeResponse,
    LogReadingResponse,
    LogSearchParams,
    LogsReadingResponse,
    NameListResponse,
)

router = APIRouter(
    responses=error_responses(401, 403, 404),
)


async def _get_consolidated_data(
    dbm: DatabaseManager,
    repo_id: str,
    get_data_func,
    page_params,
    **kwargs,
) -> NameListResponse:
    data, pagination = await get_data_func(
        dbm,
        repo_id,
        page=page_params.page,
        page_size=page_params.page_size,
        **kwargs,
    )
    return NameListResponse.build(data, pagination)


@router.get(
    "/repos/{repo_id}/logs/actions/types",
    summary="Get log action types",
    operation_id="get_log_action_types",
    responses=error_responses(401, 403, 404),
    tags=["logs"],
)
async def get_log_action_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
    category: str = None,
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_action_types,
        page_params,
        action_category=category,
    )


@router.get(
    "/repos/{repo_id}/logs/actions/categories",
    summary="Get log action categories",
    operation_id="get_log_action_categories",
    tags=["logs"],
)
async def get_log_action_categories(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_action_categories,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/actors/types",
    summary="Get log actor types",
    operation_id="get_log_actor_types",
    tags=["logs"],
)
async def get_log_actor_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_actor_types,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/actors/extras",
    summary="Get log actor extra field names",
    operation_id="get_log_actor_extras",
    tags=["logs"],
    response_model=NameListResponse,
)
async def get_log_actor_extras(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_actor_extra_fields,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/resources/types",
    summary="Get log resource types",
    operation_id="get_log_resource_types",
    tags=["logs"],
)
async def get_log_resource_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_resource_types,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/resources/extras",
    summary="Get log resource extra field names",
    operation_id="get_log_resource_extras",
    tags=["logs"],
    response_model=NameListResponse,
)
async def get_log_resource_extras(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_resource_extra_fields,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/tags/types",
    summary="Get log tag types",
    operation_id="get_log_tag_types",
    tags=["logs"],
)
async def get_log_tag_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_tag_types,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/sources",
    summary="Get log source field names",
    operation_id="get_log_source_fields",
    tags=["logs"],
    response_model=NameListResponse,
)
async def get_log_source_fields(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_source_fields,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/details",
    summary="Get log detail field names",
    operation_id="get_log_detail_fields",
    tags=["logs"],
    response_model=NameListResponse,
)
async def get_log_detail_fields(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_detail_fields,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/attachments/types",
    summary="Get log attachment types",
    operation_id="get_log_attachment_types",
    tags=["logs"],
    response_model=NameListResponse,
)
async def get_log_attachment_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_attachment_types,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/attachments/mime-types",
    summary="Get log attachment MIME types",
    operation_id="get_log_attachment_mime_types",
    tags=["logs"],
    response_model=NameListResponse,
)
async def get_log_attachment_mime_types(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    page_params: Annotated[PagePaginationParams, Depends()],
) -> NameListResponse:
    return await _get_consolidated_data(
        dbm,
        repo_id,
        service.get_log_attachment_mime_types,
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/nodes",
    summary="Get log nodes",
    operation_id="get_log_nodes",
    tags=["logs"],
)
async def get_log_nodes(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    root: bool = False,
    parent_node_ref: str = None,
    page_params: Annotated[PagePaginationParams, Depends()] = PagePaginationParams(),
) -> LogNodeListResponse:
    if root and parent_node_ref is not None:
        raise ValidationError(
            "Parameters 'root' and 'parent_node_ref' are mutually exclusive."
        )

    if root:
        filter_args = {"parent_node_ref": None}
    elif parent_node_ref:
        filter_args = {"parent_node_ref": parent_node_ref}
    else:
        filter_args = {}

    nodes, pagination = await service.get_log_nodes(
        dbm,
        repo_id,
        page=page_params.page,
        page_size=page_params.page_size,
        **filter_args,
    )
    return LogNodeListResponse.build(nodes, pagination)


@router.get(
    "/repos/{repo_id}/logs/nodes/ref:{node_ref}",
    summary="Get a log node",
    operation_id="get_log_node",
    tags=["logs"],
)
async def get_log_node(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    node_ref: Annotated[str, Path(title="Node ref")],
) -> LogNodeResponse:
    node = await service.get_log_node(dbm, repo_id, node_ref)
    return LogNodeResponse.from_node(node)


@router.post(
    "/repos/{repo_id}/logs",
    status_code=201,
    summary="Create a log",
    operation_id="create_log",
    responses=error_responses(400),
    tags=["logs"],
)
async def create_log(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsWrite(),
    repo_id: str,
    log_req: LogCreationRequest,
) -> LogCreationResponse:
    log_id = await service.save_log(dbm, repo_id, log_req.to_log())
    return LogCreationResponse(id=log_id)


@router.post(
    "/repos/{repo_id}/logs/{log_id}/attachments",
    status_code=204,
    response_class=Response,
    summary="Add a file attachment to a log",
    operation_id="add_log_attachment",
    responses=error_responses(400, 413),
    tags=["logs"],
)
async def add_attachment(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsWrite(),
    repo_id: str,
    log_id: Annotated[
        str, Path(title="Log ID", description="The ID of the log to attach the file to")
    ],
    file: UploadFile,
    type: Annotated[
        str,
        Form(
            title="Attachment type",
            description="The 'functional' type of the attachment",
            json_schema_extra={"example": "Configuration file"},
            pattern=IDENTIFIER_PATTERN_STRING,
        ),
    ],
    name: Annotated[
        str,
        Form(
            title="Attachment name",
            description="The name of the attachment. If not provided, the name of the uploaded file will be used.",
            json_schema_extra={"example": "config.json"},
        ),
    ] = None,
    description: Annotated[
        str,
        Form(
            title="Attachment description",
            description="An optional description of the attachment",
            json_schema_extra={"example": "Configuration file"},
        ),
    ] = None,
    mime_type: Annotated[
        str,
        Form(
            title="Attachment MIME type",
            description="The MIME type of the attachment. If not provided, the MIME type of the uploaded "
            "file will be used.",
            json_schema_extra={"example": "application/json"},
        ),
    ] = None,
) -> None:
    config = get_config()
    data = await file.read(config.attachment_max_size + 1)
    if len(data) > config.attachment_max_size:
        raise PayloadTooLarge(
            f"Attachment size exceeds the maximum allowed size ({config.attachment_max_size} bytes)"
        )
    await service.save_log_attachment(
        dbm,
        repo_id,
        log_id,
        description=description,
        name=name or file.filename,
        type=type,
        mime_type=mime_type or file.content_type or "application/octet-stream",
        data=data,
    )


@router.get(
    "/repos/{repo_id}/logs/{log_id}",
    summary="Get a log",
    operation_id="get_log",
    tags=["logs"],
    status_code=200,
)
async def get_log(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    log_id: Annotated[str, Path(title="Log ID")],
) -> LogReadingResponse:
    log = await service.get_log(
        dbm,
        repo_id,
        log_id,
        authorized_nodes=authenticated.permissions.logs.get_repo_nodes(repo_id),
    )
    return LogReadingResponse.from_log(log)


@router.get(
    "/repos/{repo_id}/logs/{log_id}/attachments/{attachment_idx}",
    summary="Download a log attachment",
    operation_id="get_log_attachment",
    tags=["logs"],
    response_class=Response,
    responses={
        200: {
            "description": (
                "Attachment content. The actual MIME type will be the MIME type "
                "of the attachment when it was uploaded."
            ),
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary", "example": None}
                }
            },
        },
    },
)
async def get_log_attachment(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    log_id: str = Path(title="Log ID"),
    attachment_idx: int = Path(
        title="Attachment index",
        description="The index of the attachment in the log's attachments list (starts from 0)",
    ),
):
    attachment = await service.get_log_attachment(dbm, repo_id, log_id, attachment_idx)
    return Response(
        content=attachment.data,
        media_type=attachment.mime_type,
        headers={"Content-Disposition": f"attachment; filename={attachment.name}"},
    )


@router.get(
    "/repos/{repo_id}/logs", summary="Get logs", operation_id="get_logs", tags=["logs"]
)
async def get_logs(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: AuthorizedOnLogsRead(),
    repo_id: str,
    search_params: Annotated[LogSearchParams, Depends()],
    page_params: Annotated[CursorPaginationParams, Depends()],
) -> LogsReadingResponse:
    # FIXME: we must check that "until" is greater than "since"
    logs, next_cursor = await service.get_logs(
        dbm,
        repo_id,
        authorized_nodes=authenticated.permissions.logs.get_repo_nodes(repo_id),
        action_type=search_params.action_type,
        action_category=search_params.action_category,
        source=search_params.source,
        actor_type=search_params.actor_type,
        actor_name=search_params.actor_name,
        actor_ref=search_params.actor_ref,
        actor_extra=search_params.actor_extra,
        resource_type=search_params.resource_type,
        resource_name=search_params.resource_name,
        resource_ref=search_params.resource_ref,
        resource_extra=search_params.resource_extra,
        details=search_params.details,
        tag_type=search_params.tag_type,
        tag_name=search_params.tag_name,
        tag_ref=search_params.tag_ref,
        attachment_name=search_params.attachment_name,
        attachment_description=search_params.attachment_description,
        attachment_type=search_params.attachment_type,
        attachment_mime_type=search_params.attachment_mime_type,
        node_ref=search_params.node_ref,
        since=search_params.since,
        until=search_params.until,
        limit=page_params.limit,
        pagination_cursor=page_params.cursor,
    )
    return LogsReadingResponse.build(logs, next_cursor)
