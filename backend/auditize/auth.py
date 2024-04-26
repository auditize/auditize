import dataclasses

from fastapi import Depends, Request

from auditize.common.db import DatabaseManager, get_dbm
from auditize.common.exceptions import UnknownModelException, AuthenticationFailure
from auditize.integrations.service import get_integration_by_token
from auditize.users.service import get_user_by_session_token

_BEARER_PREFIX = "Bearer "


@dataclasses.dataclass
class Authenticated:
    name: str


def _get_authorization_bearer(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise LookupError("Authorization header not found")
    if not authorization.startswith(_BEARER_PREFIX):
        raise LookupError("Authorization header is not a Bearer token")
    return authorization[len(_BEARER_PREFIX):]


async def authenticate_integration(dbm: DatabaseManager, request: Request) -> Authenticated:
    try:
        token = _get_authorization_bearer(request)
    except LookupError as e:
        raise AuthenticationFailure(str(e))

    try:
        integration = await get_integration_by_token(dbm, token)
    except UnknownModelException:
        raise AuthenticationFailure("Invalid integration token")

    return Authenticated(name=integration.name)


def looks_like_integration_auth(request: Request) -> bool:
    return bool(request.headers.get("Authorization"))


async def authenticate_user(dbm: DatabaseManager, request: Request) -> Authenticated:
    if not request.cookies:
        raise AuthenticationFailure()

    session_token = request.cookies.get("token")
    if not session_token:
        raise AuthenticationFailure()

    user = await get_user_by_session_token(dbm, session_token)

    return Authenticated(name=user.email)


def looks_like_user_auth(request: Request) -> bool:
    return bool(request.cookies.get("token"))


async def get_authenticated(
    dbm: DatabaseManager = Depends(get_dbm), request: Request = Depends()
) -> Authenticated:
    if looks_like_integration_auth(request):
        return await authenticate_integration(dbm, request)

    if looks_like_user_auth(request):
        return await authenticate_user(dbm, request)

    raise AuthenticationFailure()
