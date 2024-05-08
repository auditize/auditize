from datetime import datetime, timedelta

from jose import ExpiredSignatureError, JWTError, jwt

from auditize.common.utils import now
from auditize.config import get_config
from auditize.exceptions import AuthenticationFailure

_JWT_SUB_PREFIX = "user_email:"


# NB: make this function public so can can test valid JWT tokens but signed with another key
def generate_session_token_payload(user_email: str) -> tuple[dict, datetime]:
    expires_at = now() + timedelta(seconds=get_config().user_session_token_lifetime)
    payload = {"sub": f"{_JWT_SUB_PREFIX}{user_email}", "exp": expires_at}
    return payload, expires_at


def generate_session_token(user_email) -> tuple[str, datetime]:
    config = get_config()
    payload, expires_at = generate_session_token_payload(user_email)
    token = jwt.encode(payload, config.jwt_signing_key, algorithm="HS256")
    return token, expires_at


def get_user_email_from_session_token(token: str) -> str:
    # Load JWT token
    try:
        payload = jwt.decode(token, get_config().jwt_signing_key, algorithms=["HS256"])
    except ExpiredSignatureError:
        raise AuthenticationFailure("JWT token expired")
    except JWTError:
        raise AuthenticationFailure("Cannot decode JWT token")

    # Get user email from token
    try:
        sub = payload["sub"]
    except KeyError:
        raise AuthenticationFailure("Missing 'sub' field in JWT token")
    if not sub.startswith(_JWT_SUB_PREFIX):
        raise AuthenticationFailure("Invalid 'sub' field in JWT token")
    email = sub[len(_JWT_SUB_PREFIX) :]

    return email
