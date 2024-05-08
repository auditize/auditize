import dataclasses
from typing import Annotated, Callable, Type

from fastapi import Depends
from starlette.requests import Request

from auditize.apikeys.models import Apikey
from auditize.apikeys.service import get_apikey_by_token
from auditize.auth.jwt import get_user_email_from_session_token
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import (
    AuthenticationFailure,
    PermissionDenied,
    UnknownModelException,
)
from auditize.permissions.assertions import (
    PermissionAssertion,
    can_read_logs,
    can_write_logs,
)
from auditize.permissions.models import Permissions
from auditize.users.models import User
from auditize.users.service import get_user_by_email

_BEARER_PREFIX = "Bearer "


@dataclasses.dataclass
class Authenticated:
    name: str
    user: User = None
    apikey: Apikey = None

    @classmethod
    def from_user(cls, user: User):
        return cls(name=user.email, user=user)

    @classmethod
    def from_apikey(cls, apikey: Apikey):
        return cls(name=apikey.name, apikey=apikey)

    @property
    def permissions(self) -> Permissions:
        if self.user:
            return self.user.permissions
        if self.apikey:
            return self.apikey.permissions
        raise Exception("Authenticated is neither user nor apikey")  # pragma: no cover

    def comply(self, assertion: PermissionAssertion) -> bool:
        return assertion(self.permissions)


def _get_authorization_bearer(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise LookupError("Authorization header not found")
    if not authorization.startswith(_BEARER_PREFIX):
        raise LookupError("Authorization header is not a Bearer token")
    return authorization[len(_BEARER_PREFIX) :]


async def authenticate_apikey(dbm: DatabaseManager, request: Request) -> Authenticated:
    try:
        token = _get_authorization_bearer(request)
    except LookupError as e:
        raise AuthenticationFailure(str(e))

    try:
        apikey = await get_apikey_by_token(dbm, token)
    except UnknownModelException:
        raise AuthenticationFailure("Invalid apikey token")

    return Authenticated.from_apikey(apikey)


def looks_like_apikey_auth(request: Request) -> bool:
    return bool(request.headers.get("Authorization"))


async def authenticate_user(dbm: DatabaseManager, request: Request) -> Authenticated:
    if not request.cookies:
        raise AuthenticationFailure()

    session_token = request.cookies.get("session")
    if not session_token:
        raise AuthenticationFailure()

    user_email = get_user_email_from_session_token(session_token)
    try:
        user = await get_user_by_email(dbm, user_email)
    except UnknownModelException:
        raise AuthenticationFailure("User does not longer exist")

    return Authenticated.from_user(user)


def looks_like_user_auth(request: Request) -> bool:
    return bool(request.cookies.get("session"))


async def get_authenticated(
    dbm: Annotated[DatabaseManager, Depends(get_dbm)], request: Request
) -> Authenticated:
    if looks_like_apikey_auth(request):
        return await authenticate_apikey(dbm, request)

    if looks_like_user_auth(request):
        return await authenticate_user(dbm, request)

    raise AuthenticationFailure()


def _authorized(assertion: PermissionAssertion):
    def func(authenticated: Authenticated = Depends(get_authenticated)):
        if not authenticated.comply(assertion):
            raise PermissionDenied()
        return authenticated

    return func


def _authorized_on_logs(assertion_func: Callable[[str], PermissionAssertion]):
    def func(repo_id: str, authenticated: Authenticated = Depends(get_authenticated)):
        assertion = assertion_func(repo_id)
        if not authenticated.comply(assertion):
            raise PermissionDenied()
        return authenticated

    return func


def Authorized(assertion: PermissionAssertion) -> Type[Authenticated]:  # noqa
    return Annotated[Authenticated, Depends(_authorized(assertion))]


def AuthorizedOnLogsRead() -> Type[Authenticated]:  # noqa
    return Annotated[Authenticated, Depends(_authorized_on_logs(can_read_logs))]


def AuthorizedOnLogsWrite() -> Type[Authenticated]:  # noqa
    return Annotated[Authenticated, Depends(_authorized_on_logs(can_write_logs))]
