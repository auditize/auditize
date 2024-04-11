from bson import ObjectId

from auditize.repos.models import Repo, RepoUpdate
from auditize.common.mongo import DatabaseManager
from auditize.common.exceptions import UnknownModelException
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.common.pagination.page.models import PagePaginationInfo


async def create_repo(dbm: DatabaseManager, repo: Repo):
    result = await dbm.core_db.repos.insert_one(repo.model_dump(exclude={"id"}))
    return result.inserted_id


async def update_repo(dbm: DatabaseManager, repo_id: ObjectId | str, update: RepoUpdate):
    result = await dbm.core_db.repos.update_one(
        {"_id": ObjectId(repo_id)},
        {"$set": update.model_dump(exclude_unset=True)}
    )
    if result.matched_count == 0:
        raise UnknownModelException()


async def get_repo(dbm: DatabaseManager, repo_id: ObjectId | str) -> Repo:
    result = await dbm.core_db.repos.find_one({"_id": ObjectId(repo_id)})
    if result is None:
        raise UnknownModelException()

    return Repo.model_validate(result)


async def get_repos(dbm: DatabaseManager, page: int, page_size: int) -> tuple[list[Repo], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(dbm.core_db.repos, page=page, page_size=page_size)
    return [Repo.model_validate(result) async for result in results], page_info


async def delete_repo(dbm: DatabaseManager, repo_id: ObjectId | str):
    repo_db = dbm.get_repo_db(repo_id)
    result = await dbm.core_db.repos.delete_one({"_id": ObjectId(repo_id)})
    if result.deleted_count == 0:
        raise UnknownModelException()

    repo_db.client.drop_database(repo_db.name)
