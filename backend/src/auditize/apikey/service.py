import hashlib
import secrets
from uuid import UUID

from auditize.apikey.models import Apikey, ApikeyUpdate
from auditize.auth.constants import APIKEY_SECRET_PREFIX
from auditize.database import get_dbm
from auditize.exceptions import enhance_constraint_violation_exception
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


def _hash_key(key: str) -> str:
    # Generate a non-salted hash of the key, so it can be looked up afterward
    return hashlib.sha256(key.encode()).hexdigest()


def _generate_key() -> tuple[str, str]:
    value = APIKEY_SECRET_PREFIX + secrets.token_urlsafe(32)
    return value, _hash_key(value)


async def create_apikey(apikey: Apikey) -> tuple[UUID, str]:
    await ensure_repos_in_permissions_exist(apikey.permissions)
    key, key_hash = _generate_key()
    with enhance_constraint_violation_exception("error.constraint_violation.apikey"):
        apikey_id = await create_resource_document(
            get_dbm().core_db.apikeys,
            {
                **apikey.model_dump(exclude={"id", "key_hash", "permissions"}),
                "key_hash": key_hash,
                "permissions": normalize_permissions(apikey.permissions).model_dump(),
            },
        )
    return apikey_id, key


async def update_apikey(apikey_id: UUID, update: ApikeyUpdate):
    doc_update = update.model_dump(exclude_unset=True, exclude={"permissions"})
    if update.permissions:
        apikey = await get_apikey(apikey_id)
        apikey_permissions = update_permissions(apikey.permissions, update.permissions)
        await ensure_repos_in_permissions_exist(apikey_permissions)
        doc_update["permissions"] = apikey_permissions.model_dump()

    with enhance_constraint_violation_exception("error.constraint_violation.apikey"):
        await update_resource_document(get_dbm().core_db.apikeys, apikey_id, doc_update)


async def regenerate_apikey(apikey_id: UUID) -> str:
    dbm = get_dbm()
    key, key_hash = _generate_key()
    await update_resource_document(
        dbm.core_db.apikeys, apikey_id, {"key_hash": key_hash}
    )
    return key


async def _get_apikey(filter: any) -> Apikey:
    dbm = get_dbm()
    result = await get_resource_document(dbm.core_db.apikeys, filter)
    return Apikey.model_validate(result)


async def get_apikey(apikey_id: UUID) -> Apikey:
    return await _get_apikey(apikey_id)


async def get_apikey_by_key(key: str) -> Apikey:
    return await _get_apikey({"key_hash": _hash_key(key)})


async def get_apikeys(
    query: str, page: int, page_size: int
) -> tuple[list[Apikey], PagePaginationInfo]:
    dbm = get_dbm()
    results, page_info = await find_paginated_by_page(
        dbm.core_db.apikeys,
        filter={"$text": {"$search": query}} if query else None,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )
    return [Apikey.model_validate(result) async for result in results], page_info


async def delete_apikey(apikey_id: UUID):
    dbm = get_dbm()
    await delete_resource_document(dbm.core_db.apikeys, apikey_id)


async def remove_repo_from_apikeys_permissions(repo_id: UUID):
    dbm = get_dbm()
    await remove_repo_from_permissions(dbm.core_db.apikeys, repo_id)
