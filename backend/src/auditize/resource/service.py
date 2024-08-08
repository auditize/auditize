from uuid import UUID, uuid4

from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from auditize.exceptions import ConstraintViolation, UnknownModelException


def _normalize_filter(filter: UUID | dict) -> dict:
    if isinstance(filter, UUID):
        return {"_id": filter}
    return filter


async def create_resource_document(
    collection: AsyncIOMotorCollection,
    document: dict | BaseModel,
    *,
    resource_id: UUID = None,
) -> UUID:
    if isinstance(document, BaseModel):
        document = document.model_dump(exclude={"id"})
    if not resource_id:
        resource_id = uuid4()

    try:
        result = await collection.insert_one({**document, "_id": resource_id})
    except DuplicateKeyError:
        raise ConstraintViolation()

    return result.inserted_id


async def update_resource_document(
    collection: AsyncIOMotorCollection,
    filter: UUID | dict,
    update: dict | BaseModel,
    *,
    operator="$set",
):
    if isinstance(update, BaseModel):
        update = update.model_dump(exclude_unset=True, exclude={"id"})

    try:
        result = await collection.update_one(
            _normalize_filter(filter), {operator: update}
        )
    except DuplicateKeyError:
        raise ConstraintViolation()

    if result.matched_count == 0:
        raise UnknownModelException()


async def get_resource_document(
    collection: AsyncIOMotorCollection,
    filter: UUID | dict,
    projection: dict = None,
):
    result = await collection.find_one(_normalize_filter(filter), projection=projection)
    if not result:
        raise UnknownModelException()
    return result


async def has_resource_document(
    collection: AsyncIOMotorCollection, filter: UUID | dict
) -> bool:
    try:
        await get_resource_document(collection, filter, projection={"_id": 1})
        return True
    except UnknownModelException:
        return False


async def delete_resource_document(
    collection: AsyncIOMotorCollection, filter: UUID | dict
):
    result = await collection.delete_one(_normalize_filter(filter))
    if result.deleted_count == 0:
        raise UnknownModelException()
