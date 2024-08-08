from typing import Any, Sequence
from uuid import UUID, uuid4

from auditize.database import DatabaseManager
from auditize.exceptions import UnknownModelException, ValidationError
from auditize.logi18nprofiles.models import LogTranslation
from auditize.logi18nprofiles.service import (
    does_log_i18n_profile_exist,
    get_log_i18n_profile_translation,
)
from auditize.logs.db import LogDatabase, get_log_db_for_config
from auditize.permissions.assertions import (
    can_read_logs,
    can_write_logs,
    permissions_and,
)
from auditize.permissions.models import Permissions
from auditize.permissions.operations import is_authorized
from auditize.repos.models import Repo, RepoStats, RepoStatus, RepoUpdate
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    has_resource_document,
    update_resource_document,
)
from auditize.users.models import Lang, User


async def _validate_repo(dbm: DatabaseManager, repo: Repo | RepoUpdate):
    if repo.log_i18n_profile_id:
        if not await does_log_i18n_profile_exist(dbm, repo.log_i18n_profile_id):
            raise ValidationError(
                f"Log i18n profile {repo.log_i18n_profile_id!r} does not exist"
            )


async def create_repo(
    dbm: DatabaseManager, repo: Repo, log_db: LogDatabase = None
) -> str:
    await _validate_repo(dbm, repo)
    repo_id = uuid4()
    await create_resource_document(
        dbm.core_db.repos,
        {
            **repo.model_dump(exclude={"id", "log_db_name"}),
            "log_db_name": (
                log_db.name if log_db else f"{dbm.name_prefix}_logs_{repo_id}"
            ),
        },
        resource_id=repo_id,
    )
    repo_id = str(repo_id)
    if not log_db:
        log_db = await get_log_db_for_config(dbm, repo_id)
        await log_db.setup()
    return repo_id


async def update_repo(dbm: DatabaseManager, repo_id: UUID, update: RepoUpdate):
    await _validate_repo(dbm, update)
    await update_resource_document(dbm.core_db.repos, repo_id, update)


async def get_repo(dbm: DatabaseManager, repo_id: UUID) -> Repo:
    result = await get_resource_document(dbm.core_db.repos, repo_id)
    return Repo.model_validate(result)


async def get_repo_stats(dbm: DatabaseManager, repo_id: UUID) -> RepoStats:
    logs_db = await get_log_db_for_config(dbm, repo_id)
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


async def _get_repos(
    dbm: DatabaseManager,
    filter: dict[str, Any],
    page: int,
    page_size: int,
) -> tuple[list[Repo], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        dbm.core_db.repos,
        filter=filter,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )

    return [Repo.model_validate(result) async for result in results], page_info


async def get_repos(
    dbm: DatabaseManager, query: str, page: int, page_size: int
) -> tuple[list[Repo], PagePaginationInfo]:
    return await _get_repos(
        dbm, {"$text": {"$search": query}} if query else None, page, page_size
    )


async def get_all_repos(dbm: DatabaseManager):
    results = dbm.core_db.repos.find({})
    return [Repo.model_validate(result) async for result in results]


def _get_authorized_repo_ids_for_user(
    user: User, has_read_perm: bool, has_write_perm: bool
) -> Sequence[UUID] | None:
    no_filtering_needed = any(
        (
            is_authorized(
                user.permissions, permissions_and(can_read_logs(), can_write_logs())
            ),
            (
                is_authorized(user.permissions, can_read_logs())
                and (has_read_perm and not has_write_perm)
            ),
            (
                is_authorized(user.permissions, can_write_logs())
                and (has_write_perm and not has_read_perm)
            ),
        )
    )
    if no_filtering_needed:
        return None

    return user.permissions.logs.get_repos(
        can_read=(
            has_read_perm and not is_authorized(user.permissions, can_read_logs())
        ),
        can_write=(
            has_write_perm and not is_authorized(user.permissions, can_write_logs())
        ),
    )


async def get_user_repos(
    dbm: DatabaseManager,
    *,
    user: User,
    user_can_read: bool,
    user_can_write: bool,
    page: int,
    page_size: int,
) -> tuple[list[Repo], PagePaginationInfo]:
    filter = dict[str, Any]()

    filter["status"] = (
        RepoStatus.enabled
        if user_can_write
        else {"$in": [RepoStatus.enabled, RepoStatus.readonly]}
    )

    repo_ids = _get_authorized_repo_ids_for_user(user, user_can_read, user_can_write)
    if repo_ids is not None:
        filter["_id"] = {"$in": repo_ids}

    return await _get_repos(dbm, filter, page, page_size)


async def delete_repo(dbm: DatabaseManager, repo_id: UUID):
    # avoid circular imports
    from auditize.apikeys.service import remove_repo_from_apikeys_permissions
    from auditize.logfilters.service import delete_log_filters_with_repo
    from auditize.users.service import remove_repo_from_users_permissions

    logs_db = await get_log_db_for_config(dbm, repo_id)
    await delete_resource_document(dbm.core_db.repos, repo_id)
    await logs_db.client.drop_database(logs_db.name)
    await remove_repo_from_users_permissions(dbm, repo_id)
    await remove_repo_from_apikeys_permissions(dbm, repo_id)
    await delete_log_filters_with_repo(dbm, repo_id)


async def is_log_i18n_profile_used_by_repo(
    dbm: DatabaseManager, profile_id: UUID
) -> bool:
    return await has_resource_document(
        dbm.core_db.repos, {"log_i18n_profile_id": profile_id}
    )


async def get_repo_translation(
    dbm: DatabaseManager, repo_id: UUID, lang: Lang
) -> LogTranslation:
    repo = await get_repo(dbm, repo_id)
    if not repo.log_i18n_profile_id:
        return LogTranslation()
    try:
        return await get_log_i18n_profile_translation(
            dbm, repo.log_i18n_profile_id, lang
        )
    except UnknownModelException:  # NB: this should not happen
        return LogTranslation()


async def ensure_repos_in_permissions_exist(
    dbm: DatabaseManager, permissions: Permissions
):
    for repo_id in permissions.logs.get_repos():
        try:
            await get_repo(dbm, repo_id)
        except UnknownModelException:
            raise ValidationError(
                f"Repo {repo_id} cannot be assigned in log permissions as it does not exist"
            )


async def get_retention_period_enabled_repos(dbm: DatabaseManager) -> list[Repo]:
    results = dbm.core_db.repos.find({"retention_period": {"$ne": None}})
    return [Repo.model_validate(result) async for result in results]
