import hashlib
import secrets

from bson import ObjectId

from auditize.common.db import DatabaseManager
from auditize.common.exceptions import UnknownModelException
from auditize.common.pagination.page.models import PagePaginationInfo
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.integrations.models import Integration, IntegrationUpdate
from auditize.permissions.operations import normalize_permissions, update_permissions
from auditize.repos.service import ensure_repos_in_permissions_exist


def _hash_token(token: str) -> str:
    # Generate a non-salted hash of the token, so it can be looked up afterward
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_token() -> tuple[str, str]:
    value = "intgr-" + secrets.token_urlsafe(32)
    return value, _hash_token(value)


async def create_integration(
    dbm: DatabaseManager, integration: Integration
) -> tuple[ObjectId, str]:
    await ensure_repos_in_permissions_exist(dbm, integration.permissions)
    token, token_hash = _generate_token()
    result = await dbm.core_db.integrations.insert_one(
        {
            **integration.model_dump(exclude={"id", "token_hash", "permissions"}),
            "token_hash": token_hash,
            "permissions": normalize_permissions(integration.permissions).model_dump(),
        }
    )
    return result.inserted_id, token


async def update_integration(
    dbm: DatabaseManager, integration_id: ObjectId | str, update: IntegrationUpdate
):
    doc_update = update.model_dump(exclude_unset=True, exclude={"permissions"})
    if update.permissions:
        integration = await get_integration(dbm, integration_id)
        integration_permissions = update_permissions(
            integration.permissions, update.permissions
        )
        await ensure_repos_in_permissions_exist(dbm, integration_permissions)
        doc_update["permissions"] = integration_permissions.model_dump()

    result = await dbm.core_db.integrations.update_one(
        {"_id": ObjectId(integration_id)}, {"$set": doc_update}
    )
    if result.matched_count == 0:
        raise UnknownModelException()


async def regenerate_integration_token(
    dbm: DatabaseManager, integration_id: ObjectId | str
) -> str:
    token, token_hash = _generate_token()
    result = await dbm.core_db.integrations.update_one(
        {"_id": ObjectId(integration_id)}, {"$set": {"token_hash": token_hash}}
    )
    if result.matched_count == 0:
        raise UnknownModelException()

    return token


async def get_integration(
    dbm: DatabaseManager, integration_id: ObjectId | str
) -> Integration:
    result = await dbm.core_db.integrations.find_one({"_id": ObjectId(integration_id)})
    if result is None:
        raise UnknownModelException()

    return Integration.model_validate(result)


async def get_integration_by_token(dbm: DatabaseManager, token: str) -> Integration:
    result = await dbm.core_db.integrations.find_one({"token_hash": _hash_token(token)})
    if result is None:
        raise UnknownModelException()

    return Integration.model_validate(result)


async def get_integrations(
    dbm: DatabaseManager, page: int, page_size: int
) -> tuple[list[Integration], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.integrations, sort=[("name", 1)], page=page, page_size=page_size
    )
    return [Integration.model_validate(result) async for result in results], page_info


async def delete_integration(dbm: DatabaseManager, integration_id: ObjectId | str):
    result = await dbm.core_db.integrations.delete_one(
        {"_id": ObjectId(integration_id)}
    )
    if result.deleted_count == 0:
        raise UnknownModelException()
