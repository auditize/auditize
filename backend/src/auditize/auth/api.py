from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import Response

from auditize.auth.authorizer import Authenticated, get_authenticated
from auditize.auth.jwt import generate_session_token
from auditize.common.db import DatabaseManager, get_dbm
from auditize.users import service
from auditize.users.api_models import UserAuthenticationRequest

router = APIRouter()


@router.post("/auth/user/login", summary="User log-in", tags=["users"], status_code=204)
async def login_user(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)],
    request: UserAuthenticationRequest,
    response: Response,
):
    user = await service.authenticate_user(dbm, request.email, request.password)
    token, expires_at = generate_session_token(user.email)

    response.set_cookie(
        "session",
        token,
        httponly=True,
        samesite="strict",
        secure=True,
        expires=expires_at,
    )


@router.post(
    "/auth/user/logout", summary="User log-out", tags=["users"], status_code=204
)
async def logout_user(
    authenticated: Annotated[Authenticated, Depends(get_authenticated)],
    response: Response,
):
    response.delete_cookie("session", httponly=True, samesite="strict", secure=True)
