from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.apikeys import service
from auditize.apikeys.api_models import (
    ApikeyCreationRequest,
    ApikeyCreationResponse,
    ApikeyListResponse,
    ApikeyReadingResponse,
    ApikeyRegenerationResponse,
    ApikeyUpdateRequest,
)
from auditize.apikeys.models import ApikeyUpdate
from auditize.auth.authorizer import Authenticated, Authorized
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import PermissionDenied
from auditize.helpers.api.errors import error_responses
from auditize.helpers.pagination.page.api_models import PagePaginationParams
from auditize.helpers.resources.api_models import ResourceSearchParams
from auditize.permissions.assertions import (
    can_read_apikeys,
    can_write_apikeys,
)
from auditize.permissions.operations import authorize_grant

router = APIRouter(responses=error_responses(401, 403))


def _ensure_cannot_alter_own_apikey(authenticated: Authenticated, apikey_id: str):
    if authenticated.apikey and str(authenticated.apikey.id) == apikey_id:
        raise PermissionDenied("Cannot alter own apikey")


@router.post(
    "/apikeys",
    summary="Create API key",
    tags=["apikeys"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_apikey(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_apikeys()),
    apikey: ApikeyCreationRequest,
) -> ApikeyCreationResponse:
    apikey_model = apikey.to_db_model()
    authorize_grant(authenticated.permissions, apikey_model.permissions)
    apikey_id, key = await service.create_apikey(dbm, apikey_model)
    return ApikeyCreationResponse(id=apikey_id, key=key)


@router.patch(
    "/apikeys/{apikey_id}",
    summary="Update API key",
    tags=["apikeys"],
    status_code=204,
    responses=error_responses(400, 404, 409),
)
async def update_apikey(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_apikeys()),
    apikey_id: str,
    apikey: ApikeyUpdateRequest,
):
    _ensure_cannot_alter_own_apikey(authenticated, apikey_id)
    apikey_model = ApikeyUpdate.model_validate(apikey.model_dump())
    if apikey_model.permissions:
        authorize_grant(authenticated.permissions, apikey_model.permissions)
    await service.update_apikey(dbm, apikey_id, apikey_model)


@router.get(
    "/apikeys/{apikey_id}",
    summary="Get API key",
    tags=["apikeys"],
    responses=error_responses(404),
)
async def get_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_apikeys()),
    apikey_id: str,
) -> ApikeyReadingResponse:
    apikey = await service.get_apikey(dbm, apikey_id)
    return ApikeyReadingResponse.from_db_model(apikey)


@router.get(
    "/apikeys",
    summary="List API keys",
    tags=["apikeys"],
)
async def list_apikeys(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_apikeys()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> ApikeyListResponse:
    apikeys, page_info = await service.get_apikeys(
        dbm,
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    return ApikeyListResponse.build(apikeys, page_info)


@router.delete(
    "/apikeys/{apikey_id}",
    summary="Delete API key",
    tags=["apikeys"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_apikey(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_apikeys()),
    apikey_id: str,
):
    _ensure_cannot_alter_own_apikey(authenticated, apikey_id)
    await service.delete_apikey(dbm, apikey_id)


@router.post(
    "/apikeys/{apikey_id}/key",
    summary="Re-regenerate API key secret",
    tags=["apikeys"],
    status_code=200,
    responses=error_responses(404),
)
async def regenerate_apikey(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_apikeys()),
    apikey_id: str,
) -> ApikeyRegenerationResponse:
    _ensure_cannot_alter_own_apikey(authenticated, apikey_id)
    key = await service.regenerate_apikey(dbm, apikey_id)
    return ApikeyRegenerationResponse(key=key)
