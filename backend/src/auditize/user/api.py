from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.exception import error_responses
from auditize.api.models.search import PagePaginatedSearchParams
from auditize.auth.authorizer import Authenticated, Require, RequireUser
from auditize.dependencies import get_db_session
from auditize.exceptions import PermissionDenied
from auditize.permissions.assertions import can_read_user, can_write_user
from auditize.permissions.service import authorize_grant
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

router = APIRouter(
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)
)


def _ensure_cannot_alter_own_user(authorized: Authenticated, user_id: UUID):
    if authorized.user and authorized.user.id == user_id:
        raise PermissionDenied("Cannot alter own user")


async def _ensure_cannot_update_email_of_user_with_non_grantable_permission(
    session: AsyncSession,
    authorized: Authenticated,
    user_id: UUID,
    update: UserUpdateRequest,
):
    if not update.email:
        return

    user = await service.get_user(session, user_id)
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
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponse,
    responses=error_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT),
)
async def create_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_user()))],
    user_create: UserCreate,
):
    authorize_grant(authorized.permissions, user_create.permissions)
    return await service.create_user(session, user_create)


@router.patch(
    "/users/me",
    summary="Update authenticated user",
    operation_id="update_user_me",
    tags=["user", "internal"],
    status_code=status.HTTP_200_OK,
    response_model=UserMeResponse,
    responses=error_responses(status.HTTP_400_BAD_REQUEST),
)
async def update_user_me(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireUser())],
    user_me_update: UserMeUpdateRequest,
):
    user_update = UserUpdate.model_validate(
        user_me_update.model_dump(exclude_unset=True)
    )
    user = await service.update_user(session, authorized.user.id, user_update)
    return UserMeResponse.from_user(user)


@router.patch(
    "/users/{user_id}",
    summary="Update user",
    operation_id="update_user",
    tags=["user"],
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
    responses=error_responses(
        status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT
    ),
)
async def update_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_user()))],
    user_id: UUID,
    user_update: UserUpdateRequest,
):
    _ensure_cannot_alter_own_user(authorized, user_id)
    await _ensure_cannot_update_email_of_user_with_non_grantable_permission(
        session, authorized, user_id, user_update
    )
    if user_update.permissions:
        authorize_grant(authorized.permissions, user_update.permissions)

    return await service.update_user(
        session,
        user_id,
        UserUpdate.model_validate(user_update.model_dump(exclude_unset=True)),
    )


@router.get(
    "/users/me",
    summary="Get authorized user",
    operation_id="get_user_me",
    tags=["user", "internal"],
    response_model=UserMeResponse,
)
async def get_user_me(
    authorized: Annotated[Authenticated, Depends(RequireUser())],
):
    return UserMeResponse.from_user(authorized.user)


@router.get(
    "/users/{user_id}",
    summary="Get user",
    description="Requires `user:read` permission.",
    operation_id="get_user",
    tags=["user"],
    response_model=UserResponse,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_user()))],
    user_id: UUID,
):
    return await service.get_user(session, user_id)


@router.get(
    "/users",
    summary="List users",
    description="Requires `user:read` permission.",
    operation_id="list_users",
    tags=["user"],
    response_model=UserListResponse,
)
async def list_users(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    _: Annotated[Authenticated, Depends(Require(can_read_user()))],
    params: Annotated[PagePaginatedSearchParams, Query()],
):
    users, page_info = await service.get_users(
        session,
        params.query,
        params.page,
        params.page_size,
    )
    return UserListResponse.build(users, page_info)


@router.delete(
    "/users/{user_id}",
    summary="Delete user",
    description="Requires `user:write` permission.",
    operation_id="delete_user",
    tags=["user"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(status.HTTP_404_NOT_FOUND, status.HTTP_409_CONFLICT),
)
async def delete_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(Require(can_write_user()))],
    user_id: UUID,
):
    _ensure_cannot_alter_own_user(authorized, user_id)
    await service.delete_user(session, user_id)


@router.get(
    "/users/password-reset/{token}",
    summary="Get user password-reset info",
    operation_id="get_user_password_reset_info",
    tags=["user", "internal"],
    response_model=UserPasswordResetInfoResponse,
    responses=error_responses(status.HTTP_404_NOT_FOUND),
)
async def get_user_password_reset_info(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    token: Annotated[str, Path(description="Password-reset token")],
):
    user = await service.get_user_by_password_reset_token(session, token)
    return UserPasswordResetInfoResponse.model_validate(user, from_attributes=True)


@router.post(
    "/users/password-reset/{token}",
    summary="Set user password",
    operation_id="set_user_password",
    tags=["user", "internal"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND),
)
async def set_user_password(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    token: Annotated[str, Path(description="Password-reset token")],
    request: UserPasswordResetRequest,
):
    await service.update_user_password_by_password_reset_token(
        session, token, request.password
    )


@router.post(
    "/users/forgot-password",
    summary="Send user password-reset email",
    operation_id="forgot_password",
    description="For security reasons, this endpoint will always return a 204 status code"
    "whether the provided email exists or not.",
    tags=["user", "internal"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(status.HTTP_400_BAD_REQUEST),
)
async def forgot_password(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    reset_request: UserPasswordResetRequestRequest,
):
    await service.send_user_password_reset_link(session, reset_request.email)
