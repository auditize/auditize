from fastapi import APIRouter

from auditize.logs.api_models import LogCreationRequest, LogCreationResponse, LogReadingResponse
from auditize.logs.service import save_log, get_log

router = APIRouter()


@router.post("/logs", status_code=201)
async def create_log(log_req: LogCreationRequest) -> LogCreationResponse:
    log_id = await save_log(log_req.to_log())
    return LogCreationResponse(id=log_id)


@router.get("/logs/{log_id}")
async def read_log(log_id: str) -> LogReadingResponse:
    log = await get_log(log_id)
    return LogReadingResponse.from_log(log)
