import secrets
from datetime import datetime, timedelta

from bson import ObjectId
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from auditize.common.config import get_config
from auditize.common.db import DatabaseManager
from auditize.common.email import send_email
from auditize.common.exceptions import AuthenticationFailure, UnknownModelException
from auditize.common.pagination.page.models import PagePaginationInfo
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.common.utils import now
from auditize.permissions.operations import normalize_permissions, update_permissions
from auditize.users.models import SignupToken, User, UserUpdate

_DEFAULT_SIGNUP_TOKEN_LIFETIME = 60 * 60 * 24  # 24 hours
_JWT_SUB_PREFIX = "user_email:"

password_context = CryptContext(schemes=["bcrypt"])


def _generate_signup_token() -> SignupToken:
    return SignupToken(
        token=secrets.token_hex(32),
        expires_at=now() + timedelta(seconds=_DEFAULT_SIGNUP_TOKEN_LIFETIME),
    )


def _send_signup_email(user: User):
    config = get_config()
    send_email(
        user.email,
        "Welcome to Auditize",
        f"Welcome, {user.first_name}! Please click the following link to complete your registration: "
        f"{config.base_url}/signup/{user.signup_token.token}",
    )


# NB: this function is let public to be used in tests when we have to inject
# a user directly into database (and we want to make sure that is consistently stored)
def build_document_from_user(user: User) -> dict:
    return {
        **user.model_dump(exclude={"id", "permissions"}),
        "permissions": normalize_permissions(user.permissions).model_dump(),
    }


async def save_user(dbm: DatabaseManager, user: User):
    result = await dbm.core_db.users.insert_one(build_document_from_user(user))
    return result.inserted_id


async def create_user(dbm: DatabaseManager, user: User):
    user = user.model_copy()
    user.signup_token = _generate_signup_token()
    user_id = await save_user(dbm, user)
    _send_signup_email(user)
    return user_id


async def update_user(
    dbm: DatabaseManager, user_id: ObjectId | str, update: UserUpdate
):
    doc_update = update.model_dump(exclude_unset=True, exclude={"permissions"})
    if update.permissions:
        user = await get_user(dbm, user_id)
        doc_update["permissions"] = update_permissions(
            user.permissions, update.permissions
        ).model_dump()

    result = await dbm.core_db.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": doc_update}
    )
    if result.matched_count == 0:
        raise UnknownModelException()


async def _get_user(dbm: DatabaseManager, filter: dict) -> User:
    result = await dbm.core_db.users.find_one(filter)
    if result is None:
        raise UnknownModelException()

    return User.model_validate(result)


async def get_user(dbm: DatabaseManager, user_id: ObjectId | str) -> User:
    return await _get_user(dbm, {"_id": ObjectId(user_id)})


async def get_user_by_email(dbm: DatabaseManager, email: str) -> User:
    return await _get_user(dbm, {"email": email})


def _build_signup_token_filter(token: str):
    return {"signup_token.token": token, "signup_token.expires_at": {"$gt": now()}}


async def get_user_by_signup_token(dbm: DatabaseManager, token: str) -> User:
    result = await dbm.core_db.users.find_one(_build_signup_token_filter(token))
    if result is None:
        raise UnknownModelException()

    return User.model_validate(result)


async def get_user_by_session_token(dbm: DatabaseManager, token: str) -> User:
    # Load JWT token
    try:
        payload = jwt.decode(
            token, get_config().user_session_token_signing_key, algorithms=["HS256"]
        )
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

    # Get user by email
    try:
        return await get_user_by_email(dbm, email)
    except UnknownModelException:
        raise AuthenticationFailure("User is no longer valid")


# NB: this function is let public to be used in tests and to make sure that passwords
# are hashed in a consistent way
def hash_user_password(password: str) -> str:
    return password_context.hash(password)


async def update_user_password_by_signup_token(
    dbm: DatabaseManager, token: str, password: str
):
    password_hash = hash_user_password(password)
    result = await dbm.core_db.users.update_one(
        _build_signup_token_filter(token),
        {"$set": {"password_hash": password_hash, "signup_token": None}},
    )
    if result.modified_count == 0:
        raise UnknownModelException()


async def get_users(
    dbm: DatabaseManager, page: int, page_size: int
) -> tuple[list[User], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.users, sort=[("last_name", 1)], page=page, page_size=page_size
    )
    return [User.model_validate(result) async for result in results], page_info


async def delete_user(dbm: DatabaseManager, user_id: ObjectId | str):
    result = await dbm.core_db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise UnknownModelException()


async def _authenticate_user(dbm: DatabaseManager, email: str, password: str) -> User:
    try:
        user = await get_user_by_email(dbm, email)
    except UnknownModelException:
        raise AuthenticationFailure()

    if not password_context.verify(password, user.password_hash):
        raise AuthenticationFailure()

    return user


# NB: make this function public so can can test valid JWT tokens but signed with another key
def generate_session_token_payload(user_email: str) -> tuple[dict, datetime]:
    expires_at = now() + timedelta(seconds=get_config().user_session_token_lifetime)
    payload = {"sub": f"{_JWT_SUB_PREFIX}{user_email}", "exp": expires_at}
    return payload, expires_at


def _generate_session_token(user: User) -> tuple[str, datetime]:
    config = get_config()
    payload, expires_at = generate_session_token_payload(user.email)
    token = jwt.encode(
        payload, config.user_session_token_signing_key, algorithm="HS256"
    )
    return token, expires_at


async def authenticate_user(
    dbm: DatabaseManager, email: str, password: str
) -> tuple[str, datetime]:
    user = await _authenticate_user(dbm, email, password)
    return _generate_session_token(user)
