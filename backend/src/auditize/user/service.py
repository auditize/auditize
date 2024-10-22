import secrets
from datetime import timedelta
from uuid import UUID

import bcrypt

from auditize.config import get_config
from auditize.database import DatabaseManager, get_dbm
from auditize.exceptions import (
    AuthenticationFailure,
    ConstraintViolation,
    UnknownModelException,
    enhance_constraint_violation_exception,
    enhance_unknown_model_exception,
)
from auditize.helpers.datetime import now
from auditize.helpers.email import send_email
from auditize.permissions.operations import normalize_permissions, update_permissions
from auditize.permissions.service import remove_repo_from_permissions
from auditize.repo.service import ensure_repos_in_permissions_exist
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    update_resource_document,
)
from auditize.user.models import PasswordResetToken, User, UserUpdate

_DEFAULT_PASSWORD_RESET_TOKEN_LIFETIME = 60 * 60 * 24  # 24 hours


def _generate_password_reset_token() -> PasswordResetToken:
    return PasswordResetToken(
        token=secrets.token_hex(32),
        expires_at=now() + timedelta(seconds=_DEFAULT_PASSWORD_RESET_TOKEN_LIFETIME),
    )


def _send_account_setup_email(user: User):
    config = get_config()
    send_email(
        user.email,
        "Welcome to Auditize",
        f"Welcome, {user.first_name}! Please click the following link to complete your registration: "
        f"{config.public_url}/account-setup/{user.password_reset_token.token}",
    )


# NB: this function is let public to be used in tests when we have to inject
# a user directly into database (and we want to make sure that is consistently stored)
def build_document_from_user(user: User) -> dict:
    return {
        **user.model_dump(exclude={"id", "permissions"}),
        "permissions": normalize_permissions(user.permissions).model_dump(),
    }


async def save_user(user: User) -> UUID:
    await ensure_repos_in_permissions_exist(user.permissions)
    return await create_resource_document(
        get_dbm().core_db.users, build_document_from_user(user)
    )


async def create_user(user: User) -> UUID:
    user = user.model_copy()
    user.password_reset_token = _generate_password_reset_token()
    with enhance_constraint_violation_exception("error.constraint_violation.user"):
        user_id = await save_user(user)
    _send_account_setup_email(user)
    return user_id


async def update_user(user_id: UUID, update: UserUpdate):
    doc_update = update.model_dump(
        exclude_unset=True, exclude={"permissions", "password"}
    )
    if update.permissions:
        user = await get_user(user_id)
        user_permissions = update_permissions(user.permissions, update.permissions)
        await ensure_repos_in_permissions_exist(user_permissions)
        doc_update["permissions"] = user_permissions.model_dump()
    if update.password:
        doc_update["password_hash"] = hash_user_password(update.password)

    with enhance_constraint_violation_exception("error.constraint_violation.user"):
        await update_resource_document(get_dbm().core_db.users, user_id, doc_update)


async def _get_user(filter: UUID | dict) -> User:
    result = await get_resource_document(get_dbm().core_db.users, filter)
    return User.model_validate(result)


async def get_user(user_id: UUID) -> User:
    return await _get_user(user_id)


async def get_user_by_email(email: str) -> User:
    return await _get_user({"email": email})


def _build_password_reset_token_filter(token: str):
    return {
        "password_reset_token.token": token,
        "password_reset_token.expires_at": {"$gt": now()},
    }


async def get_user_by_password_reset_token(token: str) -> User:
    with enhance_unknown_model_exception("error.invalid_password_reset_token"):
        return await _get_user(_build_password_reset_token_filter(token))


# NB: this function is let public to be used in tests and to make sure that passwords
# are hashed in a consistent way
def hash_user_password(password: str) -> str:
    # https://github.com/pyca/bcrypt/?tab=readme-ov-file#adjustable-work-factor
    # NB: we use a different number of rounds in test mode to speed up tests
    # With default rounds (12), POST /auth/user/login takes about 0.2s vs 0.001s with 4 rounds
    return bcrypt.hashpw(
        password.encode(), bcrypt.gensalt(rounds=4 if get_config().test_mode else None)
    ).decode()


async def update_user_password_by_password_reset_token(token: str, password: str):
    password_hash = hash_user_password(password)
    with enhance_unknown_model_exception("error.invalid_password_reset_token"):
        await update_resource_document(
            get_dbm().core_db.users,
            _build_password_reset_token_filter(token),
            {"password_hash": password_hash, "password_reset_token": None},
        )


async def get_users(
    query: str | None, page: int, page_size: int
) -> tuple[list[User], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        get_dbm().core_db.users,
        # NB: '@' is considered as a separator by mongo default analyzer which means that searching on
        # john.doe@example.net would search on "john" or "doe" or "example" and lead to unexpected
        # results.
        # As searching on email is a common use case, we quote the query when it contains an '@'
        # to make sure that the whole email is searched.
        filter=(
            {"$text": {"$search": query if "@" not in query else f'"{query}"'}}
            if query
            else None
        ),
        sort=[("last_name", 1), ("first_name", 1)],
        page=page,
        page_size=page_size,
    )
    return [User.model_validate(result) async for result in results], page_info


async def _forbid_last_superadmin_deletion(user_id: UUID):
    user = await get_user(user_id)
    if user.permissions.is_superadmin:
        other_superadmin = await get_dbm().core_db.users.find_one(
            {"_id": {"$ne": user_id}, "permissions.is_superadmin": True}
        )
        if not other_superadmin:
            raise ConstraintViolation(
                "Cannot delete the last user with superadmin permissions"
            )


async def delete_user(user_id: UUID):
    await _forbid_last_superadmin_deletion(user_id)
    await delete_resource_document(get_dbm().core_db.users, user_id)


async def remove_repo_from_users_permissions(repo_id: UUID):
    await remove_repo_from_permissions(get_dbm().core_db.users, repo_id)


async def authenticate_user(email: str, password: str) -> User:
    try:
        user = await get_user_by_email(email)
    except UnknownModelException:
        raise AuthenticationFailure()

    if not user.password_hash:
        raise AuthenticationFailure()

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise AuthenticationFailure()

    dbm = get_dbm()
    await update_resource_document(
        dbm.core_db.users, user.id, {"authenticated_at": now()}
    )

    return user


def _send_password_reset_link(user: User):
    config = get_config()
    send_email(
        user.email,
        "Change your password on Auditize",
        f"Please follow this link to reset your password: "
        f"{config.public_url}/password-reset/{user.password_reset_token.token}",
    )


async def send_user_password_reset_link(email: str):
    try:
        user = await get_user_by_email(email)
    except UnknownModelException:
        # in case of unknown email, just do nothing to avoid leaking information
        return
    user.password_reset_token = _generate_password_reset_token()
    await update_resource_document(
        get_dbm().core_db.users,
        user.id,
        {
            "password_reset_token": user.password_reset_token.model_dump(),
        },
    )
    _send_password_reset_link(user)
