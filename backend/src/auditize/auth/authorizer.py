import dataclasses
from typing import Annotated, Callable
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from auditize.apikey.service import get_apikey, get_apikey_by_key
from auditize.apikey.sql_models import Apikey
from auditize.auth.constants import ACCESS_TOKEN_PREFIX, APIKEY_SECRET_PREFIX
from auditize.auth.jwt import get_access_token_data, get_user_email_from_session_token
from auditize.dependencies import get_db_session
from auditize.exceptions import (
    AuthenticationFailure,
    NotFoundError,
    PermissionDenied,
)
from auditize.permissions.assertions import (
    PermissionAssertion,
    can_read_logs_from_repo,
    can_write_logs_to_repo,
)
from auditize.permissions.service import authorize_grant, build_permissions
from auditize.permissions.sql_models import Permissions
from auditize.user.service import get_user_by_email
from auditize.user.sql_models import User

_BEARER_PREFIX = "Bearer "


@dataclasses.dataclass
class AccessToken:
    apikey: Apikey
    permissions: Permissions


@dataclasses.dataclass
class Authenticated:
    name: str
    user: User = None
    apikey: Apikey = None
    access_token: AccessToken = None

    @classmethod
    def from_user(cls, user: User):
        return cls(name=user.email, user=user)

    @classmethod
    def from_apikey(cls, apikey: Apikey):
        return cls(name=apikey.name, apikey=apikey)

    @classmethod
    def from_access_token(cls, access_token: AccessToken):
        return cls(
            name=f"Access token for API key {access_token.apikey.name!r}",
            access_token=access_token,
        )

    @property
    def permissions(self) -> Permissions:
        if self.user:
            return self.user.permissions
        if self.apikey:
            return self.apikey.permissions
        if self.access_token:
            return self.access_token.permissions
        raise Exception(
            "Authenticated is neither a user, an API key nor an access token"
        )  # pragma: no cover

    def comply(self, assertion: PermissionAssertion) -> bool:
        return assertion(self.permissions)

    def ensure_user(self):
        if not self.user:
            raise PermissionDenied("This operation is only available to users")

    def ensure_apikey(self):
        if not self.apikey:
            raise PermissionDenied("This operation is only available to API keys")


def _get_authorization_bearer(request: Request) -> str | None:
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
    if not authorization.startswith(_BEARER_PREFIX):
        raise AuthenticationFailure("Authorization header is not a Bearer")
    return authorization[len(_BEARER_PREFIX) :]


async def authenticate_apikey(session: AsyncSession, key: str) -> Authenticated:
    try:
        apikey = await get_apikey_by_key(session, key)
    except NotFoundError:
        raise AuthenticationFailure("Invalid API key")

    return Authenticated.from_apikey(apikey)


async def authenticate_access_token(
    session: AsyncSession, access_token: str
) -> Authenticated:
    jwt_token = access_token[len(ACCESS_TOKEN_PREFIX) :]
    apikey_id, permissions = get_access_token_data(jwt_token)
    try:
        apikey = await get_apikey(session, apikey_id)
    except NotFoundError:
        raise AuthenticationFailure(
            "Invalid API key corresponding to access token is no longer valid"
        )

    # Make sure the permissions once granted do not exceed the ones of the original API key
    try:
        authorize_grant(apikey.permissions, permissions)
    except PermissionDenied:
        raise AuthenticationFailure(
            "The access token has more permissions than the original API key"
        )

    return Authenticated.from_access_token(
        AccessToken(apikey=apikey, permissions=build_permissions(permissions))
    )


async def authenticate_user(session: AsyncSession, request: Request) -> Authenticated:
    if not request.cookies:
        raise AuthenticationFailure()

    session_token = request.cookies.get("session")
    if not session_token:
        raise AuthenticationFailure()

    user_email = get_user_email_from_session_token(session_token)
    try:
        user = await get_user_by_email(session, user_email)
    except NotFoundError:
        raise AuthenticationFailure("User does no longer exist")

    # to be used by the lang detection mechanism
    request.state.auditize_lang = str(user.lang.value)

    return Authenticated.from_user(user)


async def get_authenticated(
    session: Annotated[AsyncSession, Depends(get_db_session)], request: Request
) -> Authenticated:
    bearer = _get_authorization_bearer(request)
    if bearer:
        if bearer.startswith(APIKEY_SECRET_PREFIX):
            return await authenticate_apikey(session, bearer)
        if bearer.startswith(ACCESS_TOKEN_PREFIX):
            return await authenticate_access_token(session, bearer)
        raise AuthenticationFailure("Invalid bearer token")

    return await authenticate_user(session, request)


class Require:
    def __init__(self, assertion: PermissionAssertion | None):
        self.assertion = assertion

    def __call__(self, authenticated: Authenticated = Depends(get_authenticated)):
        if self.assertion and not authenticated.comply(self.assertion):
            raise PermissionDenied()
        return authenticated


class RequireAuthentication(Require):
    def __init__(self):
        super().__init__(assertion=None)


class RequireUser(Require):
    def __init__(self, assertion: PermissionAssertion | None = None):
        super().__init__(assertion)

    def __call__(self, authenticated: Authenticated = Depends(get_authenticated)):
        authenticated.ensure_user()
        return super().__call__(authenticated)


class RequireApikey(Require):
    def __init__(self, assertion: PermissionAssertion | None = None):
        super().__init__(assertion)

    def __call__(self, authenticated: Authenticated = Depends(get_authenticated)):
        authenticated.ensure_apikey()
        return super().__call__(authenticated)


def _authorized_on_logs(assertion_func: Callable[[UUID], PermissionAssertion]):
    def func(repo_id: UUID, authenticated: Authenticated = Depends(get_authenticated)):
        assertion = assertion_func(repo_id)
        if not authenticated.comply(assertion):
            raise PermissionDenied()
        return authenticated

    return func


class _RequireLogPermission:
    def _get_assertion(self, repo_id: UUID) -> PermissionAssertion:
        raise NotImplementedError()

    def __call__(
        self, repo_id: UUID, authenticated: Authenticated = Depends(get_authenticated)
    ) -> Authenticated:
        if not authenticated.comply(self._get_assertion(repo_id)):
            raise PermissionDenied()
        return authenticated


class RequireLogReadPermission(_RequireLogPermission):
    def _get_assertion(self, repo_id: UUID) -> PermissionAssertion:
        return can_read_logs_from_repo(repo_id)


class RequireLogWritePermission(_RequireLogPermission):
    def _get_assertion(self, repo_id: UUID) -> PermissionAssertion:
        return can_write_logs_to_repo(repo_id)
