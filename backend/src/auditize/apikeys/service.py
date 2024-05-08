import hashlib
import secrets

from bson import ObjectId

from auditize.apikeys.models import Apikey, ApikeyUpdate
from auditize.database import DatabaseManager
from auditize.exceptions import UnknownModelException
from auditize.helpers.pagination.page.models import PagePaginationInfo
from auditize.helpers.pagination.page.service import find_paginated_by_page
from auditize.permissions.operations import normalize_permissions, update_permissions
from auditize.repos.service import ensure_repos_in_permissions_exist


def _hash_token(token: str) -> str:
    # Generate a non-salted hash of the token, so it can be looked up afterward
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_token() -> tuple[str, str]:
    value = "intgr-" + secrets.token_urlsafe(32)
    return value, _hash_token(value)


async def create_apikey(dbm: DatabaseManager, apikey: Apikey) -> tuple[str, str]:
    await ensure_repos_in_permissions_exist(dbm, apikey.permissions)
    token, token_hash = _generate_token()
    result = await dbm.core_db.apikeys.insert_one(
        {
            **apikey.model_dump(exclude={"id", "token_hash", "permissions"}),
            "token_hash": token_hash,
            "permissions": normalize_permissions(apikey.permissions).model_dump(),
        }
    )
    return str(result.inserted_id), token


async def update_apikey(dbm: DatabaseManager, apikey_id: str, update: ApikeyUpdate):
    doc_update = update.model_dump(exclude_unset=True, exclude={"permissions"})
    if update.permissions:
        apikey = await get_apikey(dbm, apikey_id)
        apikey_permissions = update_permissions(apikey.permissions, update.permissions)
        await ensure_repos_in_permissions_exist(dbm, apikey_permissions)
        doc_update["permissions"] = apikey_permissions.model_dump()

    result = await dbm.core_db.apikeys.update_one(
        {"_id": ObjectId(apikey_id)}, {"$set": doc_update}
    )
    if result.matched_count == 0:
        raise UnknownModelException()


async def regenerate_apikey_token(dbm: DatabaseManager, apikey_id: str) -> str:
    token, token_hash = _generate_token()
    result = await dbm.core_db.apikeys.update_one(
        {"_id": ObjectId(apikey_id)}, {"$set": {"token_hash": token_hash}}
    )
    if result.matched_count == 0:
        raise UnknownModelException()

    return token


async def get_apikey(dbm: DatabaseManager, apikey_id: str) -> Apikey:
    result = await dbm.core_db.apikeys.find_one({"_id": ObjectId(apikey_id)})
    if result is None:
        raise UnknownModelException()

    return Apikey.model_validate(result)


async def get_apikey_by_token(dbm: DatabaseManager, token: str) -> Apikey:
    result = await dbm.core_db.apikeys.find_one({"token_hash": _hash_token(token)})
    if result is None:
        raise UnknownModelException()

    return Apikey.model_validate(result)


async def get_apikeys(
    dbm: DatabaseManager, page: int, page_size: int
) -> tuple[list[Apikey], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.apikeys, sort=[("name", 1)], page=page, page_size=page_size
    )
    return [Apikey.model_validate(result) async for result in results], page_info


async def delete_apikey(dbm: DatabaseManager, apikey_id: str):
    result = await dbm.core_db.apikeys.delete_one({"_id": ObjectId(apikey_id)})
    if result.deleted_count == 0:
        raise UnknownModelException()
