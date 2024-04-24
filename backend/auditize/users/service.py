from datetime import datetime, timezone, timedelta
import secrets
from bson import ObjectId

from passlib.context import CryptContext

from auditize.users.models import User, UserUpdate, SignupToken
from auditize.common.db import DatabaseManager
from auditize.common.exceptions import UnknownModelException
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


async def get_user(dbm: DatabaseManager, user_id: ObjectId | str) -> User:
    result = await dbm.core_db.users.find_one({"_id": ObjectId(user_id)})
    if result is None:
        raise UnknownModelException()

    return User.model_validate(result)


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


async def update_user_password_by_signup_token(dbm: DatabaseManager, token: str, password: str):
    password_hash = password_context.hash(password)
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
