from typing import Annotated

from fastapi import APIRouter, Depends

from auditize.auth import Authenticated, Authorized
from auditize.common.db import DatabaseManager, get_dbm
from auditize.common.exceptions import PermissionDenied
from auditize.integrations import service
from auditize.integrations.api_models import (
    IntegrationCreationRequest,
    IntegrationCreationResponse,
    IntegrationListResponse,
    IntegrationReadingResponse,
    IntegrationTokenGenerationResponse,
    IntegrationUpdateRequest,
)
from auditize.permissions.assertions import (
    can_read_integrations,
    can_write_integrations,
)

router = APIRouter()


def _ensure_cannot_alter_own_integration(
    authenticated: Authenticated, integration_id: str
):
    if (
        authenticated.integration
        and str(authenticated.integration.id) == integration_id
    ):
        raise PermissionDenied("Cannot alter own integration")


@router.post(
    "/integrations",
    summary="Create integration",
    tags=["integrations"],
    status_code=201,
)
async def create_integration(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_integrations()),
    integration: IntegrationCreationRequest,
) -> IntegrationCreationResponse:
    integration_id, token = await service.create_integration(
        dbm, integration.to_db_model()
    )
    return IntegrationCreationResponse(id=integration_id, token=token)


@router.patch(
    "/integrations/{integration_id}",
    summary="Update integration",
    tags=["integrations"],
    status_code=204,
)
async def update_integration(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_integrations()),
    integration_id: str,
    integration: IntegrationUpdateRequest,
):
    _ensure_cannot_alter_own_integration(authenticated, integration_id)
    await service.update_integration(dbm, integration_id, integration.to_db_model())


@router.get(
    "/integrations/{integration_id}",
    summary="Get integration",
    tags=["integrations"],
    response_model=IntegrationReadingResponse,
)
async def get_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_integrations()),
    integration_id: str,
) -> IntegrationReadingResponse:
    integration = await service.get_integration(dbm, integration_id)
    return IntegrationReadingResponse.from_db_model(integration)


@router.get(
    "/integrations",
    summary="List integrations",
    tags=["integrations"],
    response_model=IntegrationListResponse,
)
async def list_integrations(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_integrations()),
    page: int = 1,
    page_size: int = 10,
) -> IntegrationListResponse:
    integrations, page_info = await service.get_integrations(dbm, page, page_size)
    return IntegrationListResponse.build(integrations, page_info)


@router.delete(
    "/integrations/{integration_id}",
    summary="Delete integration",
    tags=["integrations"],
    status_code=204,
)
async def delete_integration(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_integrations()),
    integration_id: str,
):
    _ensure_cannot_alter_own_integration(authenticated, integration_id)
    await service.delete_integration(dbm, integration_id)


@router.post(
    "/integrations/{integration_id}/token",
    summary="Re-regenerate integration password",
    tags=["integrations"],
    status_code=200,
)
async def regenerate_integration_token(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_integrations()),
    integration_id: str,
):
    _ensure_cannot_alter_own_integration(authenticated, integration_id)
    token = await service.regenerate_integration_token(dbm, integration_id)
    return IntegrationTokenGenerationResponse(token=token)
