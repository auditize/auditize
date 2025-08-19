import hashlib
import secrets
from typing import Any
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClientSession
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.apikey.models import Apikey, ApikeyCreate, ApikeyUpdate
from auditize.auth.constants import APIKEY_SECRET_PREFIX
from auditize.database import get_core_db
from auditize.exceptions import enhance_constraint_violation_exception
from auditize.permissions.service import (
    build_permissions,
    normalize_permissions,
    remove_repo_from_permissions,
    update_permissions,
    validate_permissions_constraints,
)
from auditize.repo.service import ensure_repos_in_permissions_exist
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.sql_service import find_paginated_by_page
from auditize.resource.sql_service import (
    delete_sql_model,
    get_sql_model,
    save_sql_model,
)


def _hash_key(key: str) -> str:
    # Generate a non-salted hash of the key, so it can be looked up afterward
    return hashlib.sha256(key.encode()).hexdigest()


def _generate_key() -> tuple[str, str]:
    value = APIKEY_SECRET_PREFIX + secrets.token_urlsafe(32)
    return value, _hash_key(value)


async def create_apikey(
    session: AsyncSession, apikey_create: ApikeyCreate
) -> tuple[Apikey, str]:
    apikey = Apikey(
        name=apikey_create.name,
        permissions=build_permissions(apikey_create.permissions),
    )
    await validate_permissions_constraints(session, apikey.permissions)
    key, key_hash = _generate_key()
    apikey.key_hash = key_hash
    await save_sql_model(session, apikey)
    return apikey, key


async def update_apikey(
    session: AsyncSession, apikey_id: UUID, apikey_update: ApikeyUpdate
) -> Apikey:
    apikey = await get_apikey(session, apikey_id)

    if apikey_update.name:
        apikey.name = apikey_update.name

    if apikey_update.permissions:
        update_permissions(apikey.permissions, apikey_update.permissions)
        await validate_permissions_constraints(session, apikey.permissions)

    with enhance_constraint_violation_exception("error.constraint_violation.apikey"):
        await save_sql_model(session, apikey)

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
    await delete_sql_model(session, Apikey, apikey_id)


async def remove_repo_from_apikeys_permissions(
    repo_id: UUID, session: AsyncIOMotorClientSession
):
    await remove_repo_from_permissions(get_core_db().apikeys, repo_id, session)
