from textwrap import dedent
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Form,
    Path,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.exception import error_responses
from auditize.api.models.cursor_pagination import CursorPaginationParams
from auditize.api.models.search import CursorPaginatedSearchParams
from auditize.api.validation import (
    IDENTIFIER_PATTERN_STRING,
)
from auditize.auth.authorizer import (
    Authenticated,
    RequireLogReadPermission,
    RequireLogWritePermission,
)
from auditize.config import get_config
from auditize.dependencies import get_db_session
from auditize.exceptions import PayloadTooLarge, ValidationError
from auditize.helpers.datetime import now
from auditize.i18n import get_request_lang
from auditize.log.csv import (
    LOG_CSV_BUILTIN_COLUMNS,
    stream_logs_as_csv,
    validate_log_csv_columns,
)
from auditize.log.models import (
    Log,
    LogActionTypeListParams,
    LogActorResponse,
    LogCreate,
    LogEntityListParams,
    LogEntityListResponse,
    LogEntityResponse,
    LogImport,
    LogListParams,
    LogListResponse,
    LogResponse,
    LogsAsCsvParams,
    LogSearchParams,
    NameListResponse,
    NameRefPairListResponse,
)
from auditize.log.service import LogService

router = APIRouter(
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
)


async def _get_aggregated_names(
    session: AsyncSession,
    repo_id: UUID,
    get_data_func_name,
    page_params: CursorPaginationParams,
    **kwargs,
) -> NameListResponse:
    service = await LogService.for_reading(session, repo_id)
    data, next_cursor = await getattr(service, get_data_func_name)(
        limit=page_params.limit,
        pagination_cursor=page_params.cursor,
        **kwargs,
    )
    return NameListResponse.build(data, next_cursor)


async def _get_aggregated_name_ref_pairs(
    session: AsyncSession,
    repo_id: UUID,
    get_data_func_name,
    params: CursorPaginatedSearchParams,
) -> NameRefPairListResponse:
    service = await LogService.for_reading(session, repo_id)
    data, next_cursor = await getattr(service, get_data_func_name)(
        query=params.query,
        limit=params.limit,
        pagination_cursor=params.cursor,
    )
    return NameRefPairListResponse.build(data, next_cursor)


@router.get(
    "/repos/{repo_id}/logs/actions/types",
    summary="List log action types",
    description="Requires `log:read` permission.",
    operation_id="list_log_action_types",
    responses=error_responses(
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
        status.HTTP_404_NOT_FOUND,
    ),
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_action_types(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    params: Annotated[LogActionTypeListParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_action_types",
        params,
        action_category=params.category,
    )


@router.get(
    "/repos/{repo_id}/logs/actions/categories",
    summary="List log action categories",
    description="Requires `log:read` permission.",
    operation_id="list_log_action_categories",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_action_categories(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_action_categories",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/actors/types",
    summary="List log actor types",
    description="Requires `log:read` permission.",
    operation_id="list_log_actor_types",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_actor_types(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_actor_types",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/actors/extras",
    summary="List log actor custom field names",
    description="Requires `log:read` permission.",
    operation_id="list_log_actor_extras",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_actor_extras(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_actor_extra_fields",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/resources/types",
    summary="List log resource types",
    description="Requires `log:read` permission.",
    operation_id="list_log_resource_types",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_resource_types(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_resource_types",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/resources/extras",
    summary="List log resource custom field names",
    description="Requires `log:read` permission.",
    operation_id="list_log_resource_extras",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_resource_extras(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_resource_extra_fields",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/tags/types",
    summary="List log tag types",
    description="Requires `log:read` permission.",
    operation_id="list_log_tag_types",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_tag_types(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_tag_types",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/sources",
    summary="List log source field names",
    description="Requires `log:read` permission.",
    operation_id="list_log_source_fields",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_source_fields(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_source_fields",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/details",
    summary="List log detail field names",
    description="Requires `log:read` permission.",
    operation_id="list_log_detail_fields",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_detail_fields(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_detail_fields",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/attachments/types",
    summary="List log attachment types",
    description="Requires `log:read` permission.",
    operation_id="list_log_attachment_types",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_attachment_types(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_attachment_types",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/attachments/mime-types",
    summary="List log attachment MIME types",
    description="Requires `log:read` permission.",
    operation_id="list_log_attachment_mime_types",
    tags=["log"],
    response_model=NameListResponse,
)
async def get_log_attachment_mime_types(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    page_params: Annotated[CursorPaginationParams, Query()],
):
    return await _get_aggregated_names(
        session,
        repo_id,
        "get_log_attachment_mime_types",
        page_params,
    )


@router.get(
    "/repos/{repo_id}/logs/actors/names",
    summary="Get aggregated list of log actor names and refs",
    description="Requires `log:read` permission.",
    operation_id="list_log_actor_names",
    tags=["log"],
    response_model=NameRefPairListResponse,
)
async def get_log_actor_names(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    params: Annotated[CursorPaginatedSearchParams, Query()],
):
    return await _get_aggregated_name_ref_pairs(
        session, repo_id, "get_log_actor_names", params
    )


@router.get(
    "/repos/{repo_id}/logs/resources/names",
    summary="Get aggregated list of log resource names and refs",
    description="Requires `log:read` permission.",
    operation_id="list_log_resource_names",
    tags=["log"],
    response_model=NameRefPairListResponse,
)
async def get_log_resource_names(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    params: Annotated[CursorPaginatedSearchParams, Query()],
):
    return await _get_aggregated_name_ref_pairs(
        session, repo_id, "get_log_resource_names", params
    )


@router.get(
    "/repos/{repo_id}/logs/tags/names",
    summary="Get aggregated list of log tag names and refs",
    description="Requires `log:read` permission.",
    operation_id="list_log_tag_names",
    tags=["log"],
    response_model=NameRefPairListResponse,
)
async def get_log_tag_names(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    params: Annotated[CursorPaginatedSearchParams, Query()],
):
    return await _get_aggregated_name_ref_pairs(
        session, repo_id, "get_log_tag_names", params
    )


@router.get(
    "/repos/{repo_id}/logs/actors/{actor_ref}",
    summary="Get log actor",
    description="Requires `log:read` permission.",
    operation_id="get_log_actor",
    tags=["log"],
    response_model=LogActorResponse,
)
async def get_log_actor(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    actor_ref: Annotated[str, Path(description="Actor ref")],
):
    service = await LogService.for_reading(session, repo_id)
    return await service.get_log_actor(actor_ref)


@router.get(
    "/repos/{repo_id}/logs/entities",
    summary="List log entities",
    description="Requires `log:read` permission.",
    operation_id="list_log_entities",
    tags=["log"],
    response_model=LogEntityListResponse,
)
async def get_log_entities(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    params: Annotated[LogEntityListParams, Query()],
):
    if params.root and params.parent_entity_ref:
        raise ValidationError(
            "Parameters 'root' and 'parent_entity_ref' are mutually exclusive"
        )

    if params.root:
        filter_args = {"parent_entity_ref": None}
    elif params.parent_entity_ref:
        filter_args = {"parent_entity_ref": params.parent_entity_ref}
    else:
        filter_args = {}

    service = await LogService.for_reading(session, repo_id)

    entities, pagination = await service.get_log_entities(
        authorized_entities=authorized.permissions.get_repo_readable_entities(repo_id),
        limit=params.limit,
        pagination_cursor=params.cursor,
        **filter_args,
    )
    return LogEntityListResponse.build(entities, pagination)


@router.get(
    "/repos/{repo_id}/logs/entities/ref:{entity_ref}",
    summary="Get log entity",
    description="Requires `log:read` permission.",
    operation_id="get_log_entity",
    tags=["log"],
    response_model=LogEntityResponse,
)
async def get_log_entity(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    entity_ref: Annotated[str, Path(description="Entity ref")],
):
    service = await LogService.for_reading(session, repo_id)
    return await service.get_log_entity(
        entity_ref,
        authorized.permissions.get_repo_readable_entities(repo_id),
    )


@router.post(
    "/repos/{repo_id}/logs",
    status_code=status.HTTP_201_CREATED,
    summary="Create a log",
    description="Requires `log:write` permission.",
    operation_id="create_log",
    responses=error_responses(status.HTTP_400_BAD_REQUEST),
    tags=["log"],
    response_model=LogResponse,
)
async def create_log(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogWritePermission())],
    repo_id: UUID,
    log_create: LogCreate,
):
    service = await LogService.for_writing(session, repo_id)
    return await service.create_log(log_create)


@router.post(
    "/repos/{repo_id}/logs/import",
    status_code=status.HTTP_201_CREATED,
    summary="Import a log",
    description=dedent("""
    Requires `log:write` permission.

    This endpoint acts like a create_log operation,
    except that extra fields such as `id` and `saved_at` may be provided.
    For classic use cases, it is recommended to use the create_log operation instead.
    """),
    operation_id="import_log",
    responses=error_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT),
    tags=["log"],
    response_model=LogResponse,
)
async def import_log(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogWritePermission())],
    repo_id: UUID,
    log_import: LogImport,
):
    service = await LogService.for_writing(session, repo_id)
    return await service.import_log(log_import)


@router.post(
    "/repos/{repo_id}/logs/{log_id}/attachments",
    summary="Add a file attachment to a log",
    description="Requires `log:write` permission.",
    operation_id="add_log_attachment",
    tags=["log"],
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    responses=error_responses(
        status.HTTP_400_BAD_REQUEST, status.HTTP_413_CONTENT_TOO_LARGE
    ),
)
async def add_attachment(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(RequireLogWritePermission())],
    repo_id: UUID,
    log_id: Annotated[
        UUID,
        Path(description="The ID of the log to attach the file to"),
    ],
    file: UploadFile,
    type: Annotated[
        str,
        Form(
            description="The 'functional' type of the attachment",
            json_schema_extra={"example": "Configuration file"},
            pattern=IDENTIFIER_PATTERN_STRING,
        ),
    ],
    name: Annotated[
        str,
        Form(
            description="The name of the attachment. If not provided, the name of the uploaded file will be used.",
            json_schema_extra={"example": "config.json"},
        ),
    ] = None,
    mime_type: Annotated[
        str,
        Form(
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
    service = await LogService.for_writing(session, repo_id)
    await service.save_log_attachment(
        log_id,
        Log.Attachment(
            name=name or file.filename,
            type=type,
            mime_type=mime_type or file.content_type or "application/octet-stream",
            data=data,
        ),
    )


class _CsvResponse(Response):
    media_type = "text/csv"


_GET_LOGS_DESCRIPTION = (
    "Requires `log:read` permission.\n"
    "\n"
    "This endpoint also accepts search on custom fields through the extra parameters:\n"
    "- `source.<custom-field>`\n"
    "- `actor.<custom-field>`\n"
    "- `resource.<custom-field>`\n"
    "- `details.<custom-field>`\n"
    "\n"
    "Example: `/repos/{repo_id}/logs?actor.role=admin`"
)


@router.get(
    "/repos/{repo_id}/logs/csv",
    summary="List logs as CSV file",
    description=_GET_LOGS_DESCRIPTION,
    operation_id="list_logs_csv",
    tags=["log"],
    response_class=_CsvResponse,
)
async def get_logs_as_csv(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: Request,
    authorized: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    params: Annotated[LogsAsCsvParams, Query()],
):
    # NB: as we cannot properly handle an error in a StreamingResponse,
    # we perform as much validation as possible before calling get_logs_as_csv
    service = await LogService.for_reading(session, repo_id)
    columns = params.columns.split(",")  # convert columns string to a list
    validate_log_csv_columns(columns)

    filename = f"auditize-logs_{repo_id}_{now().strftime('%Y%m%d%H%M%S')}.csv"

    return StreamingResponse(
        stream_logs_as_csv(
            service,
            authorized_entities=authorized.permissions.get_repo_readable_entities(
                repo_id
            ),
            search_params=LogSearchParams.model_validate(params.model_dump()),
            columns=columns,
            lang=get_request_lang(request),
        ),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get(
    "/repos/{repo_id}/logs/{log_id}",
    summary="Get log",
    description="Requires `log:read` permission.",
    operation_id="get_log",
    tags=["log"],
    status_code=status.HTTP_200_OK,
    response_model=LogResponse,
)
async def get_log(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    log_id: Annotated[UUID, Path(description="Log ID")],
):
    service = await LogService.for_reading(session, repo_id)
    return await service.get_log(
        log_id,
        authorized_entities=authorized.permissions.get_repo_readable_entities(repo_id),
    )


@router.get(
    "/repos/{repo_id}/logs/{log_id}/attachments/{attachment_idx}",
    summary="Download a log attachment",
    description="Requires `log:read` permission.",
    operation_id="get_log_attachment",
    tags=["log"],
    response_class=Response,
    responses={
        status.HTTP_200_OK: {
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
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    log_id: UUID = Path(description="Log ID"),
    attachment_idx: int = Path(
        description="The index of the attachment in the log's attachments list (starts from 0)",
    ),
):
    service = await LogService.for_reading(session, repo_id)
    attachment = await service.get_log_attachment(
        log_id,
        attachment_idx,
        authorized_entities=authorized.permissions.get_repo_readable_entities(repo_id),
    )
    return Response(
        content=attachment.data,
        media_type=attachment.mime_type,
        headers={"Content-Disposition": f"attachment; filename={attachment.name}"},
    )


@router.get(
    "/repos/{repo_id}/logs",
    summary="List logs",
    description=_GET_LOGS_DESCRIPTION,
    operation_id="list_logs",
    tags=["log"],
    response_model=LogListResponse,
)
async def get_logs(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireLogReadPermission())],
    repo_id: UUID,
    params: Annotated[LogListParams, Query()],
):
    # FIXME: we must check that "until" is greater than "since"
    service = await LogService.for_reading(session, repo_id)
    logs, next_cursor = await service.get_logs(
        authorized_entities=authorized.permissions.get_repo_readable_entities(repo_id),
        search_params=LogSearchParams.model_validate(params.model_dump()),
        limit=params.limit,
        pagination_cursor=params.cursor,
    )
    return LogListResponse.build(logs, next_cursor)
