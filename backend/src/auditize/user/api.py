from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path

from auditize.auth.authorizer import Authenticated, Authorized, get_authenticated
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import PermissionDenied
from auditize.helpers.api.errors import error_responses
from auditize.permissions.assertions import can_read_users, can_write_users
from auditize.permissions.operations import authorize_grant
from auditize.resource.api_models import ResourceSearchParams
from auditize.resource.pagination.page.api_models import PagePaginationParams
from auditize.user import service
from auditize.user.api_models import (
    UserCreationRequest,
    UserCreationResponse,
    UserListResponse,
    UserMeResponse,
    UserMeUpdateRequest,
    UserPasswordResetInfoResponse,
    UserPasswordResetRequest,
    UserPasswordResetRequestRequest,
    UserReadingResponse,
    UserUpdateRequest,
)
from auditize.user.models import User, UserUpdate

router = APIRouter(responses=error_responses(401, 403))


def _ensure_cannot_alter_own_user(authenticated: Authenticated, user_id: UUID):
    if authenticated.user and authenticated.user.id == user_id:
        raise PermissionDenied("Cannot alter own user")


@router.post(
    "/users",
    summary="Create user",
    tags=["users"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_users()),
    user: UserCreationRequest,
) -> UserCreationResponse:
    user_model = User.model_validate(user.model_dump())
    authorize_grant(authenticated.permissions, user_model.permissions)
    user_id = await service.create_user(dbm, user_model)
    return UserCreationResponse(id=user_id)


@router.patch(
    "/users/me",
    summary="Update authenticated user",
    tags=["users"],
    status_code=200,
    responses=error_responses(400),
)
async def update_user_me(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    update_request: UserMeUpdateRequest,
):
    authenticated.ensure_user()
    update = UserUpdate.model_validate(update_request.model_dump(exclude_unset=True))
    await service.update_user(dbm, authenticated.user.id, update)
    user = await service.get_user(dbm, authenticated.user.id)
    return UserMeResponse.from_user(user)


@router.patch(
    "/users/{user_id}",
    summary="Update user",
    tags=["users"],
    status_code=204,
    responses=error_responses(400, 404, 409),
)
async def update_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_users()),
    user_id: UUID,
    user: UserUpdateRequest,
):
    _ensure_cannot_alter_own_user(authenticated, user_id)

    user_model = UserUpdate.model_validate(user.model_dump(exclude_unset=True))
    if user_model.permissions:
        authorize_grant(authenticated.permissions, user_model.permissions)
    await service.update_user(dbm, user_id, user_model)


@router.get(
    "/users/me",
    summary="Get authenticated user",
    tags=["users"],
)
async def get_user_me(
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
) -> UserMeResponse:
    authenticated.ensure_user()
    return UserMeResponse.from_user(authenticated.user)


@router.get(
    "/users/{user_id}",
    summary="Get user",
    tags=["users"],
    responses=error_responses(404),
)
async def get_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_users()),
    user_id: UUID,
) -> UserReadingResponse:
    user = await service.get_user(dbm, user_id)
    return UserReadingResponse.model_validate(user.model_dump())


@router.get("/users", summary="List users", tags=["users"])
async def list_users(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_users()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> UserListResponse:
    users, page_info = await service.get_users(
        dbm,
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    return UserListResponse.build(users, page_info)


@router.delete(
    "/users/{user_id}",
    summary="Delete user",
    tags=["users"],
    status_code=204,
    responses=error_responses(404, 409),
)
async def delete_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_users()),
    user_id: UUID,
):
    _ensure_cannot_alter_own_user(authenticated, user_id)
    await service.delete_user(dbm, user_id)


@router.get(
    "/users/password-reset/{token}",
    summary="Get user password-reset info",
    tags=["users"],
    responses=error_responses(404),
)
async def get_user_password_reset_info(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    token: Annotated[str, Path(description="Password-reset token")],
) -> UserPasswordResetInfoResponse:
    user = await service.get_user_by_password_reset_token(dbm, token)
    return UserPasswordResetInfoResponse.model_validate(user.model_dump())


@router.post(
    "/users/password-reset/{token}",
    summary="Set user password",
    tags=["users"],
    status_code=204,
    responses=error_responses(400, 404),
)
async def set_user_password(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    token: Annotated[str, Path(description="Password-reset token")],
    request: UserPasswordResetRequest,
):
    await service.update_user_password_by_password_reset_token(
        dbm, token, request.password
    )


@router.post(
    "/users/forgot-password",
    summary="Send user password-reset email",
    description="For security reasons, this endpoint will always return a 204 status code"
    "whether the email exists or not.",
    tags=["users"],
    status_code=204,
    responses=error_responses(400),
)
async def forgot_password(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    reset_request: UserPasswordResetRequestRequest,
):
    await service.send_user_password_reset_link(dbm, reset_request.email)
