from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from auditize.api.exception import error_responses
from auditize.apikey.models import AccessTokenRequest, AccessTokenResponse
from auditize.auth.authorizer import (
    Authenticated,
    RequireApikey,
    RequireUser,
)
from auditize.auth.constants import ACCESS_TOKEN_PREFIX
from auditize.auth.jwt import generate_access_token, generate_session_token
from auditize.config import get_config
from auditize.dependencies import get_db_session
from auditize.exceptions import NotFoundError, ValidationError
from auditize.permissions.models import PermissionsInput
from auditize.permissions.service import authorize_grant
from auditize.repo.service import get_repo
from auditize.user import service
from auditize.user.models import UserAuthenticationRequest, UserMeResponse

router = APIRouter()


@router.post(
    "/auth/user/login",
    summary="User login",
    operation_id="user_login",
    tags=["auth", "internal"],
    status_code=status.HTTP_200_OK,
    response_model=UserMeResponse,
    responses=error_responses(
        status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED
    ),
)
async def login_user(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    request: UserAuthenticationRequest,
    response: Response,
):
    config = get_config()
    user = await service.authenticate_user(session, request.email, request.password)
    token, expires_at = generate_session_token(user.email)

    response.set_cookie(
        "session",
        token,
        expires=expires_at,
        httponly=True,
        samesite="strict",
        secure=config.cookie_secure,
    )

    return UserMeResponse.from_user(user)


@router.post(
    "/auth/user/logout",
    summary="User logout",
    operation_id="user_logout",
    tags=["auth", "internal"],
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(status.HTTP_401_UNAUTHORIZED),
)
async def logout_user(
    _: Annotated[Authenticated, Depends(RequireUser())], response: Response
):
    config = get_config()
    response.delete_cookie(
        "session", httponly=True, samesite="strict", secure=config.cookie_secure
    )


async def _validate_permissions(session: AsyncSession, permissions: PermissionsInput):
    for repo in permissions.logs.repos:
        try:
            await get_repo(session, repo.repo_id)
        except NotFoundError as exc:
            raise ValidationError(f"Repo {repo.repo_id} does not exist") from exc


@router.post(
    "/auth/access-token",
    summary="Generate access token",
    operation_id="generate_access_token",
    tags=["auth"],
    status_code=status.HTTP_200_OK,
    response_model=AccessTokenResponse,
    responses=error_responses(status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
)
async def auth_access_token(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    authorized: Annotated[Authenticated, Depends(RequireApikey())],
    request: AccessTokenRequest,
):
    await _validate_permissions(session, request.permissions)
    authorize_grant(authorized.permissions, request.permissions)
    access_token, expires_at = generate_access_token(
        authorized.apikey.id, request.permissions
    )

    return AccessTokenResponse(
        access_token=ACCESS_TOKEN_PREFIX + access_token, expires_at=expires_at
    )
