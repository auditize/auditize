from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from auditize.exceptions import ConstraintViolation, UnknownModelException


def _normalize_filter(filter: str | dict) -> dict:
    if isinstance(filter, str):
        return {"_id": ObjectId(filter)}
    return filter


async def create_resource_document(
    collection: AsyncIOMotorCollection, document: dict | BaseModel
) -> str:
    if isinstance(document, BaseModel):
        document = document.model_dump(exclude={"id"})

    try:
        result = await collection.insert_one(document)
    except DuplicateKeyError:
        raise ConstraintViolation()

    return str(result.inserted_id)


async def update_resource_document(
    collection: AsyncIOMotorCollection,
    filter: str | dict,
    update: dict | BaseModel,
    *,
    operator="$set",
):
    if isinstance(update, BaseModel):
        update = update.model_dump(exclude_none=True)

    try:
        result = await collection.update_one(
            _normalize_filter(filter), {operator: update}
        )
    except DuplicateKeyError:
        raise ConstraintViolation()

    if result.matched_count == 0:
        raise UnknownModelException()


async def get_resource_document(
    collection: AsyncIOMotorCollection, filter: str | dict, projection: dict = None
):
    result = await collection.find_one(_normalize_filter(filter), projection=projection)
    if not result:
        raise UnknownModelException()
    return result


async def delete_resource_document(
    collection: AsyncIOMotorCollection, filter: str | dict
):
    result = await collection.delete_one(_normalize_filter(filter))
    if result.deleted_count == 0:
        raise UnknownModelException()
    return result
