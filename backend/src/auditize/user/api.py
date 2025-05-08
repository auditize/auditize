from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path

from auditize.auth.authorizer import (
    Authenticated,
    Authorized,
    AuthorizedUser,
)
from auditize.exceptions import PermissionDenied
from auditize.helpers.api.errors import error_responses
from auditize.permissions.assertions import can_read_user, can_write_user
from auditize.permissions.operations import authorize_grant
from auditize.resource.api_models import ResourceSearchParams
from auditize.resource.pagination.page.api_models import PagePaginationParams
from auditize.user import service
from auditize.user.models import (
    UserCreate,
    UserListResponse,
    UserMeResponse,
    UserMeUpdateRequest,
    UserPasswordResetInfoResponse,
    UserPasswordResetRequest,
    UserPasswordResetRequestRequest,
    UserResponse,
    UserUpdate,
    UserUpdateRequest,
)

router = APIRouter(responses=error_responses(401, 403))


def _ensure_cannot_alter_own_user(authorized: Authenticated, user_id: UUID):
    if authorized.user and authorized.user.id == user_id:
        raise PermissionDenied("Cannot alter own user")


async def _ensure_cannot_update_email_of_user_with_non_grantable_permission(
    authorized: Authorized,
    user_id: UUID,
    update: UserUpdateRequest,
):
    if not update.email:
        return

    user = await service.get_user(user_id)
    if update.email != user.email:
        try:
            authorize_grant(authorized.permissions, user.permissions)
        except PermissionDenied:
            raise PermissionDenied(("error.cannot_update_user_email",))


@router.post(
    "/users",
    summary="Create user",
    description="Requires `user:write` permission.",
    operation_id="create_user",
    tags=["user"],
    status_code=201,
    responses=error_responses(400, 409),
)
async def create_user(
    authorized: Authorized(can_write_user()),
    user_create: UserCreate,
) -> UserResponse:
    authorize_grant(authorized.permissions, user_create.permissions)
    return await service.create_user(user_create)


@router.patch(
    "/users/me",
    summary="Update authenticated user",
    operation_id="update_user_me",
    tags=["user", "internal"],
    status_code=200,
    responses=error_responses(400),
)
async def update_user_me(
    authorized: AuthorizedUser(),
    user_me_update: UserMeUpdateRequest,
) -> UserMeResponse:
    user_update = UserUpdate.model_validate(
        user_me_update.model_dump(exclude_unset=True)
    )
    user = await service.update_user(authorized.user.id, user_update)
    return UserMeResponse.from_user(user)


@router.patch(
    "/users/{user_id}",
    summary="Update user",
    operation_id="update_user",
    tags=["user"],
    status_code=200,
    responses=error_responses(400, 404, 409),
)
async def update_user(
    authorized: Authorized(can_write_user()),
    user_id: UUID,
    user_update: UserUpdateRequest,
) -> UserResponse:
    _ensure_cannot_alter_own_user(authorized, user_id)
    await _ensure_cannot_update_email_of_user_with_non_grantable_permission(
        authorized, user_id, user_update
    )
    if user_update.permissions:
        authorize_grant(authorized.permissions, user_update.permissions)

    return await service.update_user(
        user_id, UserUpdate.model_validate(user_update.model_dump(exclude_unset=True))
    )


@router.get(
    "/users/me",
    summary="Get authorized user",
    operation_id="get_user_me",
    tags=["user", "internal"],
)
async def get_user_me(
    authorized: AuthorizedUser(),
) -> UserMeResponse:
    return UserMeResponse.from_user(authorized.user)


@router.get(
    "/users/{user_id}",
    summary="Get user",
    description="Requires `user:read` permission.",
    operation_id="get_user",
    tags=["user"],
    responses=error_responses(404),
)
async def get_user(_: Authorized(can_read_user()), user_id: UUID) -> UserResponse:
    return await service.get_user(user_id)


@router.get(
    "/users",
    summary="List users",
    description="Requires `user:read` permission.",
    operation_id="list_users",
    tags=["user"],
)
async def list_users(
    _: Authorized(can_read_user()),
    search_params: Annotated[ResourceSearchParams, Depends()],
    page_params: Annotated[PagePaginationParams, Depends()],
) -> UserListResponse:
    users, page_info = await service.get_users(
        query=search_params.query,
        page=page_params.page,
        page_size=page_params.page_size,
    )
    return UserListResponse.build(users, page_info)


@router.delete(
    "/users/{user_id}",
    summary="Delete user",
    description="Requires `user:write` permission.",
    operation_id="delete_user",
    tags=["user"],
    status_code=204,
    responses=error_responses(404, 409),
)
async def delete_user(
    authorized: Authorized(can_write_user()),
    user_id: UUID,
):
    _ensure_cannot_alter_own_user(authorized, user_id)
    await service.delete_user(user_id)


@router.get(
    "/users/password-reset/{token}",
    summary="Get user password-reset info",
    operation_id="get_user_password_reset_info",
    tags=["user", "internal"],
    responses=error_responses(404),
)
async def get_user_password_reset_info(
    token: Annotated[str, Path(description="Password-reset token")],
) -> UserPasswordResetInfoResponse:
    user = await service.get_user_by_password_reset_token(token)
    return UserPasswordResetInfoResponse.model_validate(user.model_dump())


@router.post(
    "/users/password-reset/{token}",
    summary="Set user password",
    operation_id="set_user_password",
    tags=["user", "internal"],
    status_code=204,
    responses=error_responses(400, 404),
)
async def set_user_password(
    token: Annotated[str, Path(description="Password-reset token")],
    request: UserPasswordResetRequest,
):
    await service.update_user_password_by_password_reset_token(token, request.password)


@router.post(
    "/users/forgot-password",
    summary="Send user password-reset email",
    operation_id="forgot_password",
    description="For security reasons, this endpoint will always return a 204 status code"
    "whether the provided email exists or not.",
    tags=["user", "internal"],
    status_code=204,
    responses=error_responses(400),
)
async def forgot_password(
    reset_request: UserPasswordResetRequestRequest,
):
    await service.send_user_password_reset_link(reset_request.email)
