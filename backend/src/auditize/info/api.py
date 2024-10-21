from fastapi import APIRouter

from auditize.auth.authorizer import Authorized
from auditize.helpers.api.errors import error_responses
from auditize.info.api_models import InfoResponse
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
async def info(authorized: Authorized()) -> InfoResponse:
    return InfoResponse(auditize_version=__version__)
