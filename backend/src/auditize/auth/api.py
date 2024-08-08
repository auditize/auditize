from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import Response

from auditize.apikey.api_models import AccessTokenRequest, AccessTokenResponse
from auditize.auth.authorizer import (
    Authorized,
    AuthorizedApikey,
)
from auditize.auth.constants import ACCESS_TOKEN_PREFIX
from auditize.auth.jwt import generate_access_token, generate_session_token
from auditize.config import get_config
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.permissions.models import Permissions
from auditize.permissions.operations import authorize_grant
from auditize.user import service
from auditize.user.api_models import UserAuthenticationRequest, UserMeResponse

router = APIRouter()


@router.post(
    "/auth/user/login",
    summary="User login",
    tags=["auth"],
    status_code=200,
    responses=error_responses(400, 401),
)
async def login_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    request: UserAuthenticationRequest,
    response: Response,
) -> UserMeResponse:
    config = get_config()
    user = await service.authenticate_user(dbm, request.email, request.password)
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
    tags=["auth"],
    status_code=204,
    responses=error_responses(401),
)
async def logout_user(
    authenticated: Authorized(),
    response: Response,
):
    response.delete_cookie("session", httponly=True, samesite="strict", secure=True)


@router.post(
    "/auth/access-token",
    summary="Generate access token",
    tags=["auth"],
    status_code=200,
    responses=error_responses(401, 403),
)
async def auth_access_token(
    authenticated: AuthorizedApikey(),
    request: AccessTokenRequest,
) -> AccessTokenResponse:
    permissions = Permissions.model_validate(request.permissions.model_dump())
    authorize_grant(authenticated.permissions, permissions)
    access_token, expires_at = generate_access_token(
        authenticated.apikey.id, permissions
    )

    return AccessTokenResponse(
        access_token=ACCESS_TOKEN_PREFIX + access_token, expires_at=expires_at
    )
