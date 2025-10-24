from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.exception import error_responses
from auditize.api.models.search import PagePaginatedSearchParams
from auditize.apikey import service
from auditize.apikey.models import (
    ApikeyCreate,
    ApikeyCreateResponse,
    ApikeyListResponse,
    ApikeyRegenerationResponse,
    ApikeyResponse,
    ApikeyUpdate,
)
from auditize.auth.authorizer import Authenticated, Require
from auditize.dependencies import get_db_session
from auditize.exceptions import PermissionDenied
from auditize.permissions.assertions import (
    can_read_apikey,
    can_write_apikey,
)
from auditize.permissions.service import authorize_grant

router = APIRouter(
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
)


def _ensure_cannot_alter_own_apikey(authorized: Authenticated, apikey_id: UUID):
    if authorized.apikey and authorized.apikey.id == apikey_id:
        raise PermissionDenied("Cannot alter own apikey")


@router.post(
    "/apikeys",
    summary="Create API key",
    description="Requires `apikey:write` permission.",
    operation_id="create_apikey",
    tags=["apikey"],
    status_code=status.HTTP_201_CREATED,
    response_model=ApikeyCreateResponse,
    responses=error_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT),
)
async def create_apikey(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_apikey()))],
    apikey_create: ApikeyCreate,
):
    authorize_grant(authorized.permissions, apikey_create.permissions)
    apikey, key = await service.create_apikey(session, apikey_create)
    return ApikeyCreateResponse(
        id=apikey.id,
        name=apikey.name,
        created_at=apikey.created_at,
        updated_at=apikey.updated_at,
        permissions=apikey.permissions,
        key=key,
    )


@router.patch(
    "/apikeys/{apikey_id}",
    summary="Update API key",
    description="Requires `apikey:write` permission.",
    operation_id="update_apikey",
    tags=["apikey"],
    status_code=status.HTTP_200_OK,
    response_model=ApikeyResponse,
    responses=error_responses(
        status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT
    ),
)
async def update_apikey(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_apikey()))],
    apikey_id: UUID,
    apikey_update: ApikeyUpdate,
):
    _ensure_cannot_alter_own_apikey(authorized, apikey_id)
    if apikey_update.permissions:
        authorize_grant(authorized.permissions, apikey_update.permissions)
    return await service.update_apikey(session, apikey_id, apikey_update)


@router.get(
    "/apikeys/{apikey_id}",
    summary="Get API key",
    description="Requires `apikey:read` permission.",
    operation_id="get_apikey",
    tags=["apikey"],
    response_model=ApikeyResponse,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_apikey(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_apikey()))],
    apikey_id: UUID,
):
    return await service.get_apikey(session, apikey_id)


@router.get(
    "/apikeys",
    summary="List API keys",
    description="Requires `apikey:read` permission.",
    operation_id="list_apikeys",
    tags=["apikey"],
    response_model=ApikeyListResponse,
)
async def list_apikeys(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_apikey()))],
    params: Annotated[PagePaginatedSearchParams, Query()],
):
    apikeys, page_info = await service.get_apikeys(
        session,
        query=params.query,
        page=params.page,
        page_size=params.page_size,
    )
    return ApikeyListResponse.build(apikeys, page_info)


@router.delete(
    "/apikeys/{apikey_id}",
    summary="Delete API key",
    description="Requires `apikey:write` permission.",
    operation_id="delete_apikey",
    tags=["apikey"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def delete_apikey(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_apikey()))],
    apikey_id: UUID,
):
    _ensure_cannot_alter_own_apikey(authorized, apikey_id)
    await service.delete_apikey(session, apikey_id)


@router.post(
    "/apikeys/{apikey_id}/key",
    summary="Re-generate API key secret",
    description="Requires `apikey:write` permission.",
    operation_id="generate_apikey_new_secret",
    tags=["apikey"],
    status_code=status.HTTP_200_OK,
    response_model=ApikeyRegenerationResponse,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def regenerate_apikey(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_apikey()))],
    apikey_id: UUID,
):
    _ensure_cannot_alter_own_apikey(authorized, apikey_id)
    key = await service.regenerate_apikey(session, apikey_id)
    return ApikeyRegenerationResponse(key=key)
