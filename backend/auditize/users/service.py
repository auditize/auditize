from datetime import datetime, timezone, timedelta
import secrets
from bson import ObjectId

from passlib.context import CryptContext
from jose import JWTError, jwt

from auditize.users.models import User, UserUpdate, SignupToken
from auditize.common.db import DatabaseManager
from auditize.common.exceptions import UnknownModelException, AuthenticationFailure
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.common.pagination.page.models import PagePaginationInfo
from auditize.common.config import get_config
from auditize.common.email import send_email

DEFAULT_SIGNUP_TOKEN_LIFETIME = 60 * 60 * 24  # 24 hours


password_context = CryptContext(schemes=["bcrypt"])


def _generate_signup_token() -> SignupToken:
    return SignupToken(
        token=secrets.token_hex(32),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=DEFAULT_SIGNUP_TOKEN_LIFETIME)
    )


def _send_signup_email(user: User):
    config = get_config()
    send_email(
        user.email,
        "Welcome to Auditize",
        f"Welcome, {user.first_name}! Please click the following link to complete your registration: "
        f"{config.base_url}/signup/{user.signup_token.token}"
    )


async def create_user(dbm: DatabaseManager, user: User):
    user = user.model_copy()
    user.signup_token = _generate_signup_token()
    result = await dbm.core_db.users.insert_one(user.model_dump(exclude={"id"}))
    _send_signup_email(user)
    return result.inserted_id


async def update_user(dbm: DatabaseManager, user_id: ObjectId | str, update: UserUpdate):
    result = await dbm.core_db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update.model_dump(exclude_unset=True)}
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
    return {
        "signup_token.token": token,
        "signup_token.expires_at": {"$gt": datetime.now(timezone.utc)}
    }


async def get_user_by_signup_token(dbm: DatabaseManager, token: str) -> User:
    result = await dbm.core_db.users.find_one(_build_signup_token_filter(token))
    if result is None:
        raise UnknownModelException()

    return User.model_validate(result)


# NB: this function is let public to be used in tests and to make sure that passwords
# are hashed in a consistent way
def hash_user_password(password: str) -> str:
    return password_context.hash(password)


async def update_user_password_by_signup_token(dbm: DatabaseManager, token: str, password: str):
    password_hash = hash_user_password(password)
    result = await dbm.core_db.users.update_one(
        _build_signup_token_filter(token),
        {"$set": {"password_hash": password_hash, "signup_token": None}}
    )
    if result.modified_count == 0:
        raise UnknownModelException()


async def get_users(dbm: DatabaseManager, page: int, page_size: int) -> tuple[list[User], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.users,
        sort=[("last_name", 1)], page=page, page_size=page_size
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


def _generate_user_token(user: User) -> tuple[str, datetime]:
    config = get_config()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=config.user_token_lifetime)
    token = jwt.encode(
        {
            "sub": f"user_email:{user.email}",
            "exp": expires_at
        },
        config.user_token_signing_key, algorithm="HS256"
    )
    return token, expires_at


async def user_log_in(dbm: DatabaseManager, email: str, password: str) -> tuple[str, datetime]:
    user = await _authenticate_user(dbm, email, password)
    return _generate_user_token(user)
