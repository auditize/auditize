from typing import Sequence

from bson import ObjectId

from auditize.repos.models import Repo, RepoUpdate, RepoStats
from auditize.logs.db import get_logs_db
from auditize.common.db import DatabaseManager
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


async def get_repo_stats(dbm: DatabaseManager, repo_id: ObjectId | str) -> RepoStats:
    logs_db = await get_logs_db(dbm, repo_id)
    results = await logs_db.logs.aggregate([
        {
            "$group": {
                "_id": None,
                "first_log_date": {"$min": "$saved_at"},
                "last_log_date": {"$max": "$saved_at"},
                "count": {"$count": {}},
            }
        }
    ]).to_list(None)

    stats = RepoStats()

    if results:
        stats.first_log_date = results[0]["first_log_date"]
        stats.last_log_date = results[0]["last_log_date"]
        stats.log_count = results[0]["count"]

    db_stats = await logs_db.db.command("dbstats")
    stats.storage_size = int(db_stats["storageSize"])

    return stats


async def get_repos(
    dbm: DatabaseManager, *, page: int, page_size: int, repo_ids: Sequence[ObjectId | str] = None
) -> tuple[list[Repo], PagePaginationInfo]:
    # TODO: implement this as a join with the authenticated permissions
    if repo_ids:
        filter = {"_id": {"$in": list(map(ObjectId, repo_ids))}}
    else:
        filter = None
    results, page_info = await find_paginated_by_page(
        dbm.core_db.repos,
        filter=filter,
        sort=[("name", 1)], page=page, page_size=page_size
    )
    return [Repo.model_validate(result) async for result in results], page_info


async def delete_repo(dbm: DatabaseManager, repo_id: ObjectId | str):
    logs_db = await get_logs_db(dbm, repo_id)
    result = await dbm.core_db.repos.delete_one({"_id": ObjectId(repo_id)})
    if result.deleted_count == 0:
        raise UnknownModelException()

    logs_db.client.drop_database(logs_db.name)
