from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from auditize.auth.authorizer import Authenticated, Authorized, get_authenticated
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import PermissionDenied
from auditize.helpers.api.errors import error_responses
from auditize.helpers.pagination.page.api_models import PagePaginationParams
from auditize.helpers.resources.api_models import ResourceSearchParams
from auditize.permissions.assertions import can_read_users, can_write_users
from auditize.permissions.operations import authorize_grant
from auditize.users import service
from auditize.users.api_models import (
    UserCreationRequest,
    UserCreationResponse,
    UserListResponse,
    UserMeResponse,
    UserMeUpdateRequest,
    UserReadingResponse,
    UserSignupInfoResponse,
    UserSignupSetPasswordRequest,
    UserUpdateRequest,
)
from auditize.users.models import UserUpdate

router = APIRouter(responses=error_responses(401, 403))


def _ensure_cannot_alter_own_user(authenticated: Authenticated, user_id: str):
    if authenticated.user and str(authenticated.user.id) == user_id:
        raise PermissionDenied("Cannot alter own user")


def _ensure_authenticated_as_user(authenticated: Authenticated):
    if not authenticated.user:
        raise PermissionDenied("This endpoint is only available for users")


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
    user_model = user.to_db_model()
    authorize_grant(authenticated.permissions, user_model.permissions)
    user_id = await service.create_user(dbm, user_model)
    return UserCreationResponse(id=user_id)


@router.patch(
    "/users/me",
    summary="Update authenticated user",
    tags=["users"],
    status_code=204,
    responses=error_responses(400),
)
async def update_user_me(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    user: UserMeUpdateRequest,
):
    _ensure_authenticated_as_user(authenticated)
    user_model = UserUpdate.model_validate(user.model_dump())
    await service.update_user(dbm, authenticated.user.id, user_model)


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
    user_id: str,
    user: UserUpdateRequest,
):
    _ensure_cannot_alter_own_user(authenticated, user_id)

    user_model = UserUpdate.model_validate(user.model_dump())
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
    _ensure_authenticated_as_user(authenticated)
    return UserMeResponse.from_db_model(authenticated.user)


@router.get(
    "/users/{user_id}",
    summary="Get user",
    tags=["users"],
    responses=error_responses(404),
)
async def get_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    authenticated: Authorized(can_read_users()),
    user_id: str,
) -> UserReadingResponse:
    user = await service.get_user(dbm, user_id)
    return UserReadingResponse.from_db_model(user)


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
    user_id: str,
):
    _ensure_cannot_alter_own_user(authenticated, user_id)
    await service.delete_user(dbm, user_id)


@router.get(
    "/users/signup/{token}",
    summary="Get user signup info",
    tags=["users"],
    responses=error_responses(404),
)
async def get_user_signup_info(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    token: Annotated[str, Path(description="Signup token")],
) -> UserSignupInfoResponse:
    user = await service.get_user_by_signup_token(dbm, token)
    return UserSignupInfoResponse.from_db_model(user)


@router.post(
    "/users/signup/{token}",
    summary="Set user password",
    tags=["users"],
    status_code=204,
    responses=error_responses(400, 404),
)
async def set_user_password(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    token: Annotated[str, Path(description="Signup token")],
    request: UserSignupSetPasswordRequest,
):
    await service.update_user_password_by_signup_token(dbm, token, request.password)
