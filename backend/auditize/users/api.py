from typing import Annotated

from fastapi import APIRouter, Depends, Response

from auditize.users.api_models import (
    UserCreationRequest, UserCreationResponse, UserUpdateRequest, UserReadingResponse,
    UserListResponse, UserSignupInfoResponse, UserSignupSetPasswordRequest,
    UserAuthenticationRequest
)
from auditize.users import service
from auditize.common.db import DatabaseManager, get_dbm

router = APIRouter()


@router.post(
    "/users",
    summary="Create user",
    tags=["users"],
    status_code=201
)
async def create_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], user: UserCreationRequest
) -> UserCreationResponse:
    user_id = await service.create_user(dbm, user.to_db_model())
    return UserCreationResponse(id=user_id)


@router.patch(
    "/users/{user_id}",
    summary="Update user",
    tags=["repos"],
    status_code=204
)
async def update_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    user_id: str, user: UserUpdateRequest
):
    await service.update_user(dbm, user_id, user.to_db_model())
    return None


@router.get(
    "/users/{user_id}",
    summary="Get user",
    tags=["users"],
    response_model=UserReadingResponse
)
async def get_repo(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    user_id: str
) -> UserReadingResponse:
    user = await service.get_user(dbm, user_id)
    return UserReadingResponse.from_db_model(user)


@router.get(
    "/users",
    summary="List users",
    tags=["users"],
    response_model=UserListResponse
)
async def list_users(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    page: int = 1, page_size: int = 10
) -> UserListResponse:
    users, page_info = await service.get_users(dbm, page, page_size)
    return UserListResponse.build(users, page_info)


@router.delete(
    "/users/{user_id}",
    summary="Delete user",
    tags=["users"],
    status_code=204
)
async def delete_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], user_id: str
):
    await service.delete_user(dbm, user_id)


@router.get(
    "/users/signup/{token}",
    summary="Get user signup info",
    tags=["users"],
    response_model=UserSignupInfoResponse
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
    status_code=204
)
async def set_user_password(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], token: str,
    request: UserSignupSetPasswordRequest
):
    await service.update_user_password_by_signup_token(dbm, token, request.password)


@router.post(
    "/users/login",
    summary="User log-in",
    tags=["users"],
    status_code=204
)
async def login_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    request: UserAuthenticationRequest,
    response: Response
):
    token, expires_at = await service.authenticate_user(dbm, request.email, request.password)
    response.set_cookie("session", token, httponly=True, samesite="strict", secure=True, expires=expires_at)
