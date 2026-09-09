import json
from datetime import datetime, timedelta
from uuid import UUID

from joserfc import jwk, jwt
from joserfc.errors import ClaimError, ExpiredTokenError, JoseError

from auditize.config import get_config
from auditize.exceptions import AuthenticationFailure
from auditize.helpers.datetime import now
from auditize.permissions.models import PermissionsInput

_SUB_PREFIX_SESSION_TOKEN = "user_email:"
_SUB_PREFIX_ACCESS_TOKEN = "apikey_id:"


def _generate_jwt_payload(data, lifetime) -> tuple[dict, datetime]:
    expires_at = now() + timedelta(seconds=lifetime)
    return {**data, "exp": expires_at}, expires_at


def _sign_jwt_token(payload: dict) -> str:
    return jwt.encode(
        {"alg": "HS256"}, payload, jwk.import_key(get_config().jwt_signing_key, "oct")
    )


def _get_jwt_token_payload(token: str) -> dict:
    # Load JWT token
    try:
        token = jwt.decode(token, jwk.import_key(get_config().jwt_signing_key, "oct"))
    except JoseError:
        raise AuthenticationFailure("Cannot decode JWT token")

    # Validate JWT token is not expired and sub field is present
    claims_requests = jwt.JWTClaimsRegistry(sub={"essential": True})
    try:
        claims_requests.validate(token.claims)
    except ExpiredTokenError:
        raise AuthenticationFailure("JWT token expired")
    except ClaimError as exc:
        raise AuthenticationFailure(f"JWT token is invalid: {exc}")

    return token.claims


# NB: make this function public so we can test valid JWT tokens but signed with another key
def generate_session_token_payload(user_email: str) -> tuple[dict, datetime]:
    return _generate_jwt_payload(
        {"sub": f"{_SUB_PREFIX_SESSION_TOKEN}{user_email}"},
        get_config().user_session_token_lifetime,
    )


def generate_session_token(user_email) -> tuple[str, datetime]:
    payload, expires_at = generate_session_token_payload(user_email)
    return _sign_jwt_token(payload), expires_at


def get_user_email_from_session_token(token: str) -> str:
    payload = _get_jwt_token_payload(token)
    sub = payload["sub"]

    if not sub.startswith(_SUB_PREFIX_SESSION_TOKEN):
        raise AuthenticationFailure("Invalid 'sub' field in JWT token")
    email = sub[len(_SUB_PREFIX_SESSION_TOKEN) :]

    return email


def generate_access_token_payload(
    apikey_id: UUID, permissions: PermissionsInput
) -> tuple[dict, datetime]:
    return _generate_jwt_payload(
        {
            "sub": _SUB_PREFIX_ACCESS_TOKEN + str(apikey_id),
            # NB: this data will be serialized to JSON by authlib.jose using json.dumps internally,
            # unfortunately json.dumps does not support UUID serialization, that's why we
            # have to do this dump->load extra step to get UUID instances turned into strings
            "permissions": json.loads(permissions.model_dump_json()),
        },
        get_config().access_token_lifetime,
    )


def generate_access_token(
    apikey_id: UUID, permissions: PermissionsInput
) -> tuple[str, datetime]:
    payload, expires_at = generate_access_token_payload(apikey_id, permissions)
    return _sign_jwt_token(payload), expires_at


def get_access_token_data(token: str) -> tuple[UUID, PermissionsInput]:
    payload = _get_jwt_token_payload(token)
    sub = payload["sub"]

    if not sub.startswith(_SUB_PREFIX_ACCESS_TOKEN):
        raise AuthenticationFailure("Invalid 'sub' field in JWT token")
    apikey_id = sub[len(_SUB_PREFIX_ACCESS_TOKEN) :]

    permissions = PermissionsInput.model_validate(payload["permissions"])

    return UUID(apikey_id), permissions
