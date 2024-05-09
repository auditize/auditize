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
from auditize.auth.authorizer import Authenticated, Authorized
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import PermissionDenied
from auditize.permissions.assertions import (
    can_read_apikeys,
    can_write_apikeys,
)
from auditize.permissions.operations import authorize_grant

router = APIRouter()


def _ensure_cannot_alter_own_apikey(authenticated: Authenticated, apikey_id: str):
    if authenticated.apikey and str(authenticated.apikey.id) == apikey_id:
        raise PermissionDenied("Cannot alter own apikey")


@router.post(
    "/apikeys",
    summary="Create apikey",
    tags=["apikeys"],
    status_code=201,
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
    summary="Update apikey",
    tags=["apikeys"],
    status_code=204,
)
async def update_apikey(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_apikeys()),
    apikey_id: str,
    apikey: ApikeyUpdateRequest,
):
    _ensure_cannot_alter_own_apikey(authenticated, apikey_id)
    apikey_model = apikey.to_db_model()
    if apikey_model.permissions:
        authorize_grant(authenticated.permissions, apikey_model.permissions)
    await service.update_apikey(dbm, apikey_id, apikey_model)


@router.get(
    "/apikeys/{apikey_id}",
    summary="Get apikey",
    tags=["apikeys"],
    response_model=ApikeyReadingResponse,
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
    summary="List apikeys",
    tags=["apikeys"],
    response_model=ApikeyListResponse,
)
async def list_apikeys(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_apikeys()),
    page: int = 1,
    page_size: int = 10,
) -> ApikeyListResponse:
    apikeys, page_info = await service.get_apikeys(dbm, page, page_size)
    return ApikeyListResponse.build(apikeys, page_info)


@router.delete(
    "/apikeys/{apikey_id}",
    summary="Delete apikey",
    tags=["apikeys"],
    status_code=204,
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
    summary="Re-regenerate apikey",
    tags=["apikeys"],
    status_code=200,
)
async def regenerate_apikey(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_apikeys()),
    apikey_id: str,
):
    _ensure_cannot_alter_own_apikey(authenticated, apikey_id)
    key = await service.regenerate_apikey(dbm, apikey_id)
    return ApikeyRegenerationResponse(key=key)
