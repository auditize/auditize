import hashlib
import secrets
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.models.page_pagination import PagePaginationInfo
from auditize.apikey.models import ApikeyCreate, ApikeyUpdate
from auditize.apikey.sql_models import Apikey
from auditize.auth.constants import APIKEY_SECRET_PREFIX
from auditize.database.sql.service import (
    find_paginated_by_page,
    get_sql_model,
    save_sql_model,
)
from auditize.exceptions import ConstraintViolation, ValidationError
from auditize.permissions.service import (
    build_permissions,
    update_permissions,
)


def _hash_key(key: str) -> str:
    # Generate a non-salted hash of the key, so it can be looked up afterward
    return hashlib.sha256(key.encode()).hexdigest()


def _generate_key() -> tuple[str, str]:
    value = APIKEY_SECRET_PREFIX + secrets.token_urlsafe(32)
    return value, _hash_key(value)


def _build_apikey_constraint_rules(
    apikey: ApikeyCreate | ApikeyUpdate,
) -> dict[str, Exception]:
    return {
        "fk_permissions_repo_log_repo_id": ValidationError(
            f"One or more repositories in the permissions do not exist"
        ),
        "ix_apikey_name": ConstraintViolation(
            ("error.constraint_violation.apikey", {"name": apikey.name}),
        ),
    }


async def create_apikey(
    session: AsyncSession, apikey_create: ApikeyCreate
) -> tuple[Apikey, str]:
    apikey = Apikey(
        name=apikey_create.name,
        permissions=build_permissions(apikey_create.permissions),
    )
    key, key_hash = _generate_key()
    apikey.key_hash = key_hash
    await save_sql_model(
        session, apikey, constraint_rules=_build_apikey_constraint_rules(apikey_create)
    )
    return apikey, key


async def update_apikey(
    session: AsyncSession, apikey_id: UUID, apikey_update: ApikeyUpdate
) -> Apikey:
    apikey = await get_apikey(session, apikey_id)

    if apikey_update.name:
        apikey.name = apikey_update.name

    if apikey_update.permissions:
        update_permissions(apikey.permissions, apikey_update.permissions)

    await save_sql_model(
        session, apikey, constraint_rules=_build_apikey_constraint_rules(apikey_update)
    )

    return apikey


async def regenerate_apikey(session: AsyncSession, apikey_id: UUID) -> str:
    apikey = await get_apikey(session, apikey_id)
    key, key_hash = _generate_key()
    apikey.key_hash = key_hash
    await save_sql_model(session, apikey)
    return key


async def _get_apikey(session: AsyncSession, filter: UUID | Any) -> Apikey:
    return await get_sql_model(session, Apikey, filter)


async def get_apikey(session: AsyncSession, apikey_id: UUID) -> Apikey:
    return await _get_apikey(session, apikey_id)


async def get_apikey_by_key(session: AsyncSession, key: str) -> Apikey:
    return await _get_apikey(session, Apikey.key_hash == _hash_key(key))


async def get_apikeys(
    session: AsyncSession, query: str, page: int, page_size: int
) -> tuple[list[Apikey], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        session,
        Apikey,
        filter=Apikey.name.ilike(f"%{query}%") if query else None,
        order_by=Apikey.name.asc(),
        page=page,
        page_size=page_size,
    )
    return results, page_info


async def delete_apikey(session: AsyncSession, apikey_id: UUID):
    apikey = await get_apikey(session, apikey_id)
    await session.delete(apikey.permissions)
    await session.delete(apikey)
    await session.commit()
