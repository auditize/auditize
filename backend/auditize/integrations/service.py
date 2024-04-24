import secrets
from bson import ObjectId

from passlib.context import CryptContext

from auditize.integrations.models import Integration, IntegrationUpdate
from auditize.common.db import DatabaseManager
from auditize.common.exceptions import UnknownModelException
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.common.pagination.page.models import PagePaginationInfo


token_context = CryptContext(schemes=["bcrypt"])


def _generate_token() -> tuple[str, str]:
    value = "intgr-" + secrets.token_urlsafe(32)
    return value, token_context.hash(value)


async def create_integration(dbm: DatabaseManager, integration: Integration) -> tuple[ObjectId, str]:
    integration = integration.model_copy()
    token, token_hash = _generate_token()
    integration.token_hash = token_hash
    result = await dbm.core_db.integrations.insert_one(integration.model_dump(exclude={"id"}))
    return result.inserted_id, token


async def update_integration(dbm: DatabaseManager, integration_id: ObjectId | str, update: IntegrationUpdate):
    result = await dbm.core_db.integrations.update_one(
        {"_id": ObjectId(integration_id)},
        {"$set": update.model_dump(exclude_unset=True)}
    )
    if result.matched_count == 0:
        raise UnknownModelException()


async def regenerate_integration_token(dbm: DatabaseManager, integration_id: ObjectId | str) -> str:
    token, token_hash = _generate_token()
    result = await dbm.core_db.integrations.update_one(
        {"_id": ObjectId(integration_id)},
        {"$set": {"token_hash": token_hash}}
    )
    if result.matched_count == 0:
        raise UnknownModelException()

    return token


async def get_integration(dbm: DatabaseManager, integration_id: ObjectId | str) -> Integration:
    result = await dbm.core_db.integrations.find_one({"_id": ObjectId(integration_id)})
    if result is None:
        raise UnknownModelException()

    return Integration.model_validate(result)


async def get_integrations(dbm: DatabaseManager, page: int, page_size: int) \
        -> tuple[list[Integration], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.integrations,
        sort=[("name", 1)], page=page, page_size=page_size
    )
    return [Integration.model_validate(result) async for result in results], page_info


async def delete_integration(dbm: DatabaseManager, integration_id: ObjectId | str):
    result = await dbm.core_db.integrations.delete_one({"_id": ObjectId(integration_id)})
    if result.deleted_count == 0:
        raise UnknownModelException()
