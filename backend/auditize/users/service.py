from bson import ObjectId

from auditize.users.models import User, UserUpdate
from auditize.common.db import DatabaseManager
from auditize.common.exceptions import UnknownModelException
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.common.pagination.page.models import PagePaginationInfo


async def create_user(dbm: DatabaseManager, user: User):
    result = await dbm.core_db.users.insert_one(user.model_dump(exclude={"id"}))
    return result.inserted_id


async def update_user(dbm: DatabaseManager, user_id: ObjectId | str, update: UserUpdate):
    result = await dbm.core_db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update.model_dump(exclude_unset=True)}
    )
    if result.matched_count == 0:
        raise UnknownModelException()


async def get_user(dbm: DatabaseManager, user_id: ObjectId | str) -> User:
    result = await dbm.core_db.users.find_one({"_id": ObjectId(user_id)})
    if result is None:
        raise UnknownModelException()

    return User.model_validate(result)


async def get_users(dbm: DatabaseManager, page: int, page_size: int) -> tuple[list[User], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.users,
        sort=[("last_name", 1)], page=page, page_size=page_size
    )
    return [User.model_validate(result) async for result in results], page_info


async def delete_user(dbm: DatabaseManager, user_id: ObjectId | str):
    result = await dbm.core_db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise UnknownModelException()
