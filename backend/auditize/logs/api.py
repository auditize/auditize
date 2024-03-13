from typing import Annotated

from fastapi import APIRouter, UploadFile, Form, Response

from auditize.logs.api_models import LogCreationRequest, LogCreationResponse, LogReadingResponse
from auditize.logs import service

router = APIRouter()


@router.post("/logs", status_code=201)
async def create_log(log_req: LogCreationRequest) -> LogCreationResponse:
    log_id = await service.save_log(log_req.to_log())
    return LogCreationResponse(id=log_id)


@router.post("/logs/{log_id}/attachments")
async def add_attachment(
        log_id: str,
        file: UploadFile,
        type: Annotated[str, Form()],
        name: Annotated[str, Form()] = None,
        mime_type: Annotated[str, Form()] = None
):
    await service.save_log_attachment(
        log_id,
        name or file.filename,
        type,
        mime_type or file.content_type,
        await file.read()
    )


@router.get("/logs/{log_id}")
async def get_log(log_id: str) -> LogReadingResponse:
    log = await service.get_log(log_id)
    return LogReadingResponse.from_log(log)


@router.get("/logs/{log_id}/attachments/{attachment_idx}")
async def get_log_attachment(log_id: str, attachment_idx: int):
    attachment = await service.get_log_attachment(log_id, attachment_idx)
    return Response(
        content=attachment.data,
        media_type=attachment.mime_type,
        headers={"Content-Disposition": f"attachment; filename={attachment.name}"}
    )
