import secrets
from datetime import timedelta

import bcrypt
from bson import ObjectId

from auditize.config import get_config
from auditize.database import DatabaseManager
from auditize.exceptions import (
    AuthenticationFailure,
    ConstraintViolation,
    UnknownModelException,
)
from auditize.helpers.datetime import now
from auditize.helpers.email import send_email
from auditize.helpers.pagination.page.models import PagePaginationInfo
from auditize.helpers.pagination.page.service import find_paginated_by_page
from auditize.helpers.resources.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    update_resource_document,
)
from auditize.permissions.operations import normalize_permissions, update_permissions
from auditize.repos.service import ensure_repos_in_permissions_exist
from auditize.users.models import SignupToken, User, UserUpdate

_DEFAULT_SIGNUP_TOKEN_LIFETIME = 60 * 60 * 24  # 24 hours


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


async def save_user(dbm: DatabaseManager, user: User) -> str:
    await ensure_repos_in_permissions_exist(dbm, user.permissions)
    return await create_resource_document(
        dbm.core_db.users, build_document_from_user(user)
    )


async def create_user(dbm: DatabaseManager, user: User) -> str:
    user = user.model_copy()
    user.signup_token = _generate_signup_token()
    user_id = await save_user(dbm, user)
    _send_signup_email(user)
    return user_id


async def update_user(dbm: DatabaseManager, user_id: str, update: UserUpdate):
    doc_update = update.model_dump(exclude_unset=True, exclude={"permissions"})
    if update.permissions:
        user = await get_user(dbm, user_id)
        user_permissions = update_permissions(user.permissions, update.permissions)
        await ensure_repos_in_permissions_exist(dbm, user_permissions)
        doc_update["permissions"] = user_permissions.model_dump()

    await update_resource_document(dbm.core_db.users, user_id, doc_update)


async def _get_user(dbm: DatabaseManager, filter: dict) -> User:
    result = await get_resource_document(dbm.core_db.users, filter)
    return User.model_validate(result)


async def get_user(dbm: DatabaseManager, user_id: str) -> User:
    return await _get_user(dbm, {"_id": ObjectId(user_id)})


async def get_user_by_email(dbm: DatabaseManager, email: str) -> User:
    return await _get_user(dbm, {"email": email})


def _build_signup_token_filter(token: str):
    return {"signup_token.token": token, "signup_token.expires_at": {"$gt": now()}}


async def get_user_by_signup_token(dbm: DatabaseManager, token: str) -> User:
    return await _get_user(dbm, _build_signup_token_filter(token))


# NB: this function is let public to be used in tests and to make sure that passwords
# are hashed in a consistent way
def hash_user_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


async def update_user_password_by_signup_token(
    dbm: DatabaseManager, token: str, password: str
):
    password_hash = hash_user_password(password)
    await update_resource_document(
        dbm.core_db.users,
        _build_signup_token_filter(token),
        {"password_hash": password_hash, "signup_token": None},
    )


async def get_users(
    dbm: DatabaseManager, page: int, page_size: int
) -> tuple[list[User], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.users, sort=[("last_name", 1)], page=page, page_size=page_size
    )
    return [User.model_validate(result) async for result in results], page_info


async def _forbid_last_superadmin_deletion(dbm: DatabaseManager, user_id: str):
    user = await get_user(dbm, user_id)
    if user.permissions.is_superadmin:
        other_superadmin = await dbm.core_db.users.find_one(
            {"_id": {"$ne": ObjectId(user_id)}, "permissions.is_superadmin": True}
        )
        if not other_superadmin:
            raise ConstraintViolation(
                "Cannot delete the last user with superadmin permissions"
            )


async def delete_user(dbm: DatabaseManager, user_id: str):
    await _forbid_last_superadmin_deletion(dbm, user_id)
    await delete_resource_document(dbm.core_db.users, user_id)


async def authenticate_user(dbm: DatabaseManager, email: str, password: str) -> User:
    try:
        user = await get_user_by_email(dbm, email)
    except UnknownModelException:
        raise AuthenticationFailure()

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise AuthenticationFailure()

    return user
