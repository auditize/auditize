from typing import Annotated

from fastapi import APIRouter, UploadFile, Form, Response, Path, Depends

from auditize.logs.api_models import LogCreationRequest, LogCreationResponse, LogReadingResponse
from auditize.logs import service
from auditize.common.mongo import Database, get_db

router = APIRouter()


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
    tags=["logs"]
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
