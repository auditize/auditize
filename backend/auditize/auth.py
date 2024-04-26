import dataclasses

from fastapi import Depends, Request

from auditize.common.db import DatabaseManager, get_dbm
from auditize.common.exceptions import UnknownModelException
from auditize.integrations.service import get_integration_by_token


_BEARER_PREFIX = "Bearer "


def _get_authorization_bearer(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise LookupError("Authorization header not found")
    if not authorization.startswith(_BEARER_PREFIX):
        raise LookupError("Authorization header is not a Bearer token")
    return authorization[len(_BEARER_PREFIX):]


@dataclasses.dataclass
class Authenticated:
    name: str


async def try_authenticated_using_integration(dbm: DatabaseManager, request: Request):
    try:
        token = _get_authorization_bearer(request)
    except LookupError:
        return None
    try:
        integration = await get_integration_by_token(dbm, token)
    except UnknownModelException:
        return None
    return Authenticated(name=integration.name)


async def get_authenticated(
    dbm: DatabaseManager = Depends(get_dbm), request: Request = Depends()
):
    authenticated = await try_authenticated_using_integration(dbm, request)
    if authenticated is not None:
        return authenticated
    return None
