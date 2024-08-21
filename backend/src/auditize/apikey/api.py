from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from auditize.apikey import service
from auditize.apikey.api_models import (
    ApikeyCreationRequest,
    ApikeyCreationResponse,
    ApikeyListResponse,
    ApikeyReadingResponse,
    ApikeyRegenerationResponse,
    ApikeyUpdateRequest,
)
from auditize.apikey.models import Apikey, ApikeyUpdate
from auditize.auth.authorizer import Authenticated, Authorized
from auditize.exceptions import PermissionDenied
from auditize.helpers.api.errors import error_responses
from auditize.permissions.assertions import (
    can_read_apikey,
    can_write_apikey,
)
from auditize.permissions.operations import authorize_grant
from auditize.resource.api_models import ResourceSearchParams
from auditize.resource.pagination.page.api_models import PagePaginationParams

router = APIRouter(responses=error_responses(401, 403))


def _ensure_cannot_alter_own_apikey(authorized: Authenticated, apikey_id: UUID):
    if authorized.apikey and authorized.apikey.id == apikey_id:
        raise PermissionDenied("Cannot alter own apikey")


@router.post(
    "/apikeys",
    summary="Create API key",
    description="Requires `apikey:write` permission.",
    operation_id="create_apikey",
    tags=["apikey"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_apikey(
    authorized: Authorized(can_write_apikey()),
    apikey: ApikeyCreationRequest,
) -> ApikeyCreationResponse:
    apikey_model = Apikey.model_validate(apikey.model_dump())
    authorize_grant(authorized.permissions, apikey_model.permissions)
    apikey_id, key = await service.create_apikey(apikey_model)
    return ApikeyCreationResponse(id=apikey_id, key=key)


@router.patch(
    "/apikeys/{apikey_id}",
    summary="Update API key",
    description="Requires `apikey:write` permission.",
    operation_id="update_apikey",
    tags=["apikey"],
    status_code=204,
    responses=error_responses(400, 404, 409),
)
async def update_apikey(
    authorized: Authorized(can_write_apikey()),
    apikey_id: UUID,
    apikey: ApikeyUpdateRequest,
):
    _ensure_cannot_alter_own_apikey(authorized, apikey_id)
    apikey_model = ApikeyUpdate.model_validate(apikey.model_dump(exclude_unset=True))
    if apikey_model.permissions:
        authorize_grant(authorized.permissions, apikey_model.permissions)
    await service.update_apikey(apikey_id, apikey_model)


@router.get(
    "/apikeys/{apikey_id}",
    summary="Get API key",
    description="Requires `apikey:read` permission.",
    operation_id="get_apikey",
    tags=["apikey"],
    responses=error_responses(404),
)
async def get_repo(
    authorized: Authorized(can_read_apikey()),
    apikey_id: UUID,
) -> ApikeyReadingResponse:
    apikey = await service.get_apikey(apikey_id)
    return ApikeyReadingResponse.model_validate(apikey.model_dump())


@router.get(
    "/apikeys",
    summary="List API keys",
    description="Requires `apikey:read` permission.",
    operation_id="list_apikeys",
    tags=["apikey"],
)
async def list_apikeys(
    authorized: Authorized(can_read_apikey()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> ApikeyListResponse:
    apikeys, page_info = await service.get_apikeys(
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    return ApikeyListResponse.build(apikeys, page_info)


@router.delete(
    "/apikeys/{apikey_id}",
    summary="Delete API key",
    description="Requires `apikey:write` permission.",
    operation_id="delete_apikey",
    tags=["apikey"],
    status_code=204,
    responses=error_responses(404),
)
async def delete_apikey(
    authorized: Authorized(can_write_apikey()),
    apikey_id: UUID,
):
    _ensure_cannot_alter_own_apikey(authorized, apikey_id)
    await service.delete_apikey(apikey_id)


@router.post(
    "/apikeys/{apikey_id}/key",
    summary="Re-generate API key secret",
    description="Requires `apikey:write` permission.",
    operation_id="generate_apikey_new_secret",
    tags=["apikey"],
    status_code=200,
    responses=error_responses(404),
)
async def regenerate_apikey(
    authorized: Authorized(can_write_apikey()),
    apikey_id: UUID,
) -> ApikeyRegenerationResponse:
    _ensure_cannot_alter_own_apikey(authorized, apikey_id)
    key = await service.regenerate_apikey(apikey_id)
    return ApikeyRegenerationResponse(key=key)
