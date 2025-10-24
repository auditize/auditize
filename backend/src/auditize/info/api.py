from typing import Annotated

from fastapi import APIRouter, Depends, status

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
    status_code=status.HTTP_200_OK,
    response_model=InfoResponse,
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def info(
    _: Annotated[Authenticated, Depends(RequireAuthentication())],
):
    return InfoResponse(auditize_version=__version__)
