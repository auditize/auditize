from typing import Sequence

from bson import ObjectId

from auditize.common.db import DatabaseManager
from auditize.common.exceptions import UnknownModelException
from auditize.common.pagination.page.models import PagePaginationInfo
from auditize.common.pagination.page.service import find_paginated_by_page
from auditize.logs.db import get_logs_db
from auditize.permissions.assertions import (
    can_read_logs,
    can_write_logs,
    permissions_and,
)
from auditize.permissions.operations import is_authorized
from auditize.repos.models import Repo, RepoStats, RepoUpdate
from auditize.users.models import User


async def create_repo(dbm: DatabaseManager, repo: Repo) -> ObjectId:
    result = await dbm.core_db.repos.insert_one(repo.model_dump(exclude={"id"}))
    return result.inserted_id


async def update_repo(
    dbm: DatabaseManager, repo_id: ObjectId | str, update: RepoUpdate
):
    result = await dbm.core_db.repos.update_one(
        {"_id": ObjectId(repo_id)}, {"$set": update.model_dump(exclude_unset=True)}
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
    results = await logs_db.logs.aggregate(
        [
            {
                "$group": {
                    "_id": None,
                    "first_log_date": {"$min": "$saved_at"},
                    "last_log_date": {"$max": "$saved_at"},
                    "count": {"$count": {}},
                }
            }
        ]
    ).to_list(None)

    stats = RepoStats()

    if results:
        stats.first_log_date = results[0]["first_log_date"]
        stats.last_log_date = results[0]["last_log_date"]
        stats.log_count = results[0]["count"]

    db_stats = await logs_db.db.command("dbstats")
    stats.storage_size = int(db_stats["storageSize"])

    return stats


def _get_authorized_repo_ids_for_user(
    user: User, has_read_perm: bool, has_write_perm: bool
) -> Sequence[str] | None:
    no_filtering_needed = any(
        (
            is_authorized(
                user.permissions, permissions_and(can_read_logs(), can_write_logs())
            ),
            is_authorized(user.permissions, can_read_logs())
            and (has_read_perm and not has_write_perm),
            is_authorized(user.permissions, can_write_logs())
            and (has_write_perm and not has_read_perm),
        )
    )
    if no_filtering_needed:
        return None

    return user.permissions.logs.get_repos(
        can_read=has_read_perm and not is_authorized(user.permissions, can_read_logs()),
        can_write=has_write_perm
        and not is_authorized(user.permissions, can_write_logs()),
    )


async def get_repos(
    dbm: DatabaseManager,
    *,
    page: int,
    page_size: int,
    user: User = None,
    user_can_read: bool = False,
    user_can_write: bool = False,
) -> tuple[list[Repo], PagePaginationInfo]:
    repo_ids = None

    if user:
        repo_ids = _get_authorized_repo_ids_for_user(
            user, user_can_read, user_can_write
        )

    if repo_ids is not None:
        filter = {"_id": {"$in": list(map(ObjectId, repo_ids))}}
    else:
        filter = None

    results, page_info = await find_paginated_by_page(
        dbm.core_db.repos,
        filter=filter,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )

    return [Repo.model_validate(result) async for result in results], page_info


async def delete_repo(dbm: DatabaseManager, repo_id: ObjectId | str):
    logs_db = await get_logs_db(dbm, repo_id)
    result = await dbm.core_db.repos.delete_one({"_id": ObjectId(repo_id)})
    if result.deleted_count == 0:
        raise UnknownModelException()

    logs_db.client.drop_database(logs_db.name)
