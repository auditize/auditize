import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import bcrypt
from motor.motor_asyncio import AsyncIOMotorClientSession
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_

from auditize.config import get_config
from auditize.database import get_core_db
from auditize.exceptions import (
    AuthenticationFailure,
    ConstraintViolation,
    UnknownModelException,
    enhance_constraint_violation_exception,
    enhance_unknown_model_exception,
)
from auditize.helpers.datetime import now
from auditize.helpers.email import send_email
from auditize.permissions.models import Permissions
from auditize.permissions.service import (
    build_permissions,
    remove_repo_from_permissions,
    update_permissions,
    validate_permissions_constraints,
)
from auditize.repo.service import ensure_repos_in_permissions_exist
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.sql_service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    create_resource_document2,
    delete_resource_document,
    get_resource_document,
    update_resource_document,
)
from auditize.resource.sql_service import (
    delete_sql_model,
    get_sql_model,
    save_sql_model,
    update_sql_model,
)
from auditize.user.models import User, UserCreate, UserUpdate

_DEFAULT_PASSWORD_RESET_TOKEN_LIFETIME = 60 * 60 * 24  # 24 hours


def _generate_password_reset_token() -> tuple[str, datetime]:
    token = secrets.token_hex(32)
    expires_at = now() + timedelta(seconds=_DEFAULT_PASSWORD_RESET_TOKEN_LIFETIME)
    return token, expires_at


def _send_account_setup_email(user: User):
    config = get_config()
    send_email(
        user.email,
        "Welcome to Auditize",
        f"Welcome, {user.first_name}! Please click the following link to complete your registration: "
        f"{config.public_url}/account-setup/{user.password_reset_token}",
    )


async def save_user(session: AsyncSession, user: User) -> User:
    await validate_permissions_constraints(session, user.permissions)
    await save_sql_model(session, user)
    return user


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    user = User(**user_create.model_dump())
    user.permissions = build_permissions(user_create.permissions)
    user.password_reset_token, user.password_reset_token_expires_at = (
        _generate_password_reset_token()
    )
    with enhance_constraint_violation_exception("error.constraint_violation.user"):
        user = await save_user(session, user)
    _send_account_setup_email(user)
    return user


async def update_user(
    session: AsyncSession, user_id: UUID, user_update: UserUpdate
) -> User:
    user = await get_user(session, user_id)
    user_updated_fields = user_update.model_dump(
        exclude_unset=True, exclude={"permissions", "password"}
    )

    if user_update.password:
        user_updated_fields["password_hash"] = hash_user_password(user_update.password)

    if user_update.permissions:
        update_permissions(user.permissions, user_update.permissions)
        await validate_permissions_constraints(session, user.permissions)

    with enhance_constraint_violation_exception("error.constraint_violation.user"):
        await update_sql_model(session, user, user_updated_fields)

    return user


async def _get_user(session: AsyncSession, filter: UUID | Any) -> User:
    return await get_sql_model(session, User, filter)


async def get_user(session: AsyncSession, user_id: UUID) -> User:
    return await _get_user(session, user_id)


async def get_user_by_email(session: AsyncSession, email: str) -> User:
    return await _get_user(session, User.email == email)


def _build_password_reset_token_filter(token: str):
    return and_(
        User.password_reset_token == token,
        User.password_reset_token_expires_at > now(),
    )


async def get_user_by_password_reset_token(session: AsyncSession, token: str) -> User:
    with enhance_unknown_model_exception("error.invalid_password_reset_token"):
        return await _get_user(session, _build_password_reset_token_filter(token))


# NB: this function is let public to be used in tests and to make sure that passwords
# are hashed in a consistent way
def hash_user_password(password: str) -> str:
    # https://github.com/pyca/bcrypt/?tab=readme-ov-file#adjustable-work-factor
    # NB: we use a different number of rounds in test mode to speed up tests
    # With default rounds (12), POST /auth/user/login takes about 0.2s vs 0.001s with 4 rounds
    return bcrypt.hashpw(
        password.encode(), bcrypt.gensalt(rounds=4 if get_config().test_mode else None)
    ).decode()


async def update_user_password_by_password_reset_token(
    session: AsyncSession, token: str, password: str
):
    password_hash = hash_user_password(password)
    with enhance_unknown_model_exception("error.invalid_password_reset_token"):
        user = await _get_user(session, _build_password_reset_token_filter(token))
    user.password_hash = password_hash
    user.password_reset_token = None
    await save_sql_model(session, user)


async def get_users(
    session: AsyncSession, query: str | None, page: int, page_size: int
) -> tuple[list[User], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        session,
        User,
        filter=(
            or_(
                User.last_name.ilike(f"%{query}%"),
                User.first_name.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%"),
            )
            if query
            else None
        ),
        order_by=(User.last_name, User.first_name),
        page=page,
        page_size=page_size,
    )
    return results, page_info


async def _forbid_last_superadmin_deletion(session: AsyncSession, user_id: UUID):
    user = await get_user(session, user_id)
    if user.permissions.is_superadmin:
        other_superadmin = await session.execute(
            select(User)
            .join(User.permissions)
            .where(User.id != user_id, Permissions.is_superadmin == True)
        )
        other_superadmin = other_superadmin.scalar()
        if not other_superadmin:
            raise ConstraintViolation(
                "Cannot delete the last user with superadmin permissions"
            )


async def delete_user(session: AsyncSession, user_id: UUID):
    await _forbid_last_superadmin_deletion(session, user_id)
    await delete_sql_model(session, User, user_id)


async def remove_repo_from_users_permissions(
    repo_id: UUID, session: AsyncIOMotorClientSession
):
    await remove_repo_from_permissions(get_core_db().users, repo_id, session)


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    try:
        user = await get_user_by_email(session, email)
    except UnknownModelException:
        raise AuthenticationFailure()

    if not user.password_hash:
        raise AuthenticationFailure()

    if not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise AuthenticationFailure()

    user.authenticated_at = now()
    await update_sql_model(session, user, {"authenticated_at": now()})

    return user


def _send_password_reset_link(user: User):
    config = get_config()
    send_email(
        user.email,
        "Change your password on Auditize",
        f"Please follow this link to reset your password: "
        f"{config.public_url}/password-reset/{user.password_reset_token}",
    )


async def send_user_password_reset_link(session: AsyncSession, email: str):
    try:
        user = await get_user_by_email(session, email)
    except UnknownModelException:
        # in case of unknown email, just do nothing to avoid leaking information
        return

    user.password_reset_token, user.password_reset_token_expires_at = (
        _generate_password_reset_token()
    )
    await save_sql_model(session, user)
    _send_password_reset_link(user)
