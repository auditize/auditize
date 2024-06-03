from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import Response

from auditize.auth.authorizer import Authenticated, get_authenticated
from auditize.auth.jwt import generate_session_token
from auditize.database import DatabaseManager, get_dbm
from auditize.helpers.api.errors import error_responses
from auditize.users import service
from auditize.users.api_models import UserAuthenticationRequest, UserMeResponse

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
    user = await service.authenticate_user(dbm, request.email, request.password)
    token, expires_at = generate_session_token(user.email)

    response.set_cookie(
        "session",
        token,
        expires=expires_at,
        httponly=True,
        samesite="strict",
        secure=True,
    )

    return UserMeResponse.from_db_model(user)


@router.post(
    "/auth/user/logout",
    summary="User logout",
    tags=["auth"],
    status_code=204,
    responses=error_responses(401),
)
async def logout_user(
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    response: Response,
):
    response.delete_cookie("session", httponly=True, samesite="strict", secure=True)
