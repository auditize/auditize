import json
from datetime import datetime, timedelta
from uuid import UUID

from authlib.jose import JsonWebToken
from authlib.jose.errors import ExpiredTokenError, JoseError

from auditize.config import get_config
from auditize.exceptions import AuthenticationFailure
from auditize.helpers.datetime import now
from auditize.permissions.models import Permissions

_SUB_PREFIX_SESSION_TOKEN = "user_email:"
_SUB_PREFIX_ACCESS_TOKEN = "apikey_id:"

jwt = JsonWebToken(["HS256"])


def _generate_jwt_payload(data, lifetime) -> tuple[dict, datetime]:
    expires_at = now() + timedelta(seconds=lifetime)
    return {**data, "exp": expires_at}, expires_at


def _sign_jwt_token(payload: dict) -> str:
    value = jwt.encode({"alg": "HS256"}, payload, key=get_config().jwt_signing_key)
    return value.decode()


def _get_jwt_token_payload(token: str) -> dict:
    # Load JWT token
    try:
        claims = jwt.decode(token, get_config().jwt_signing_key)
        claims.validate()
    except ExpiredTokenError:
        raise AuthenticationFailure("JWT token expired")
    except JoseError:
        raise AuthenticationFailure("Cannot decode JWT token")

    # Ensure the token has a 'sub' field
    if "sub" not in claims:
        raise AuthenticationFailure("Missing 'sub' field in JWT token")

    return claims


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
    apikey_id: UUID, permissions: Permissions
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
    apikey_id: UUID, permissions: Permissions
) -> tuple[str, datetime]:
    payload, expires_at = generate_access_token_payload(apikey_id, permissions)
    return _sign_jwt_token(payload), expires_at


def get_access_token_data(token: str) -> tuple[UUID, Permissions]:
    payload = _get_jwt_token_payload(token)
    sub = payload["sub"]

    if not sub.startswith(_SUB_PREFIX_ACCESS_TOKEN):
        raise AuthenticationFailure("Invalid 'sub' field in JWT token")
    apikey_id = sub[len(_SUB_PREFIX_ACCESS_TOKEN) :]

    permissions = Permissions.model_validate(payload["permissions"])

    return UUID(apikey_id), permissions
