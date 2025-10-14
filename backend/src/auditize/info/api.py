from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.api.exception import error_responses
from auditize.auth.authorizer import Authenticated, RequireAuthentication
from auditize.info.models import InfoResponse
from auditize.version import __version__

router = APIRouter()


@router.get(
    "/info",
    summary="Get Auditize information",
    operation_id="info",
    tags=["info"],
    status_code=200,
    responses=error_responses(401),
)
async def info(
    _: Annotated[Authenticated, Depends(RequireAuthentication())],
) -> InfoResponse:
    return InfoResponse(auditize_version=__version__)
