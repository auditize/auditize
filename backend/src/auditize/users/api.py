from typing import Annotated

from fastapi import APIRouter, Depends, Response

from auditize.auth.authorizer import Authenticated, Authorized, get_authenticated
from auditize.common.db import DatabaseManager, get_dbm
from auditize.common.exceptions import AuthenticationFailure, PermissionDenied
from auditize.permissions.assertions import can_read_users, can_write_users
from auditize.permissions.operations import authorize_grant
from auditize.users import service
from auditize.users.api_models import (
    UserAuthenticationRequest,
    UserCreationRequest,
    UserCreationResponse,
    UserListResponse,
    UserMeResponse,
    UserReadingResponse,
    UserSignupInfoResponse,
    UserSignupSetPasswordRequest,
    UserUpdateRequest,
)

router = APIRouter()


def _ensure_cannot_alter_own_user(authenticated: Authenticated, user_id: str):
    if authenticated.user and str(authenticated.user.id) == user_id:
        raise PermissionDenied("Cannot alter own user")


@router.post("/users", summary="Create user", tags=["users"], status_code=201)
async def create_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_users()),
    user: UserCreationRequest,
) -> UserCreationResponse:
    user_model = user.to_db_model()
    authorize_grant(authenticated.permissions, user_model.permissions)
    user_id = await service.create_user(dbm, user_model)
    return UserCreationResponse(id=user_id)


@router.patch(
    "/users/{user_id}", summary="Update user", tags=["users"], status_code=204
)
async def update_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_users()),
    user_id: str,
    user: UserUpdateRequest,
):
    _ensure_cannot_alter_own_user(authenticated, user_id)
    user_model = user.to_db_model()
    if user_model.permissions:
        authorize_grant(authenticated.permissions, user_model.permissions)
    await service.update_user(dbm, user_id, user_model)
    return None


@router.get(
    "/users/me",
    summary="Get authenticated user",
    tags=["users"],
    response_model=UserMeResponse,
)
async def get_user_me(
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
) -> UserMeResponse:
    if not authenticated.user:
        raise AuthenticationFailure()
    return UserMeResponse.from_db_model(authenticated.user)


@router.get(
    "/users/{user_id}",
    summary="Get user",
    tags=["users"],
    response_model=UserReadingResponse,
)
async def get_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_users()),
    user_id: str,
) -> UserReadingResponse:
    user = await service.get_user(dbm, user_id)
    return UserReadingResponse.from_db_model(user)


@router.get(
    "/users", summary="List users", tags=["users"], response_model=UserListResponse
)
async def list_users(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_users()),
    page: int = 1,
    page_size: int = 10,
) -> UserListResponse:
    users, page_info = await service.get_users(dbm, page, page_size)
    return UserListResponse.build(users, page_info)


@router.delete(
    "/users/{user_id}", summary="Delete user", tags=["users"], status_code=204
)
async def delete_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_write_users()),
    user_id: str,
):
    _ensure_cannot_alter_own_user(authenticated, user_id)
    await service.delete_user(dbm, user_id)


@router.get(
    "/users/signup/{token}",
    summary="Get user signup info",
    tags=["users"],
    response_model=UserSignupInfoResponse,
)
async def get_user_signup_info(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], token: str
) -> UserSignupInfoResponse:
    user = await service.get_user_by_signup_token(dbm, token)
    return UserSignupInfoResponse.from_db_model(user)


@router.post(
    "/users/signup/{token}",
    summary="Set user password",
    tags=["users"],
    status_code=204,
)
async def set_user_password(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    token: str,
    request: UserSignupSetPasswordRequest,
):
    await service.update_user_password_by_signup_token(dbm, token, request.password)


@router.post("/users/login", summary="User log-in", tags=["users"], status_code=204)
async def login_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    request: UserAuthenticationRequest,
    response: Response,
):
    token, expires_at = await service.authenticate_user(
        dbm, request.email, request.password
    )
    response.set_cookie(
        "session",
        token,
        httponly=True,
        samesite="strict",
        secure=True,
        expires=expires_at,
    )


@router.post("/users/logout", summary="User log-out", tags=["users"], status_code=204)
async def logout_user(
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    response: Response,
):
    response.delete_cookie("session", httponly=True, samesite="strict", secure=True)
