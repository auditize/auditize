from datetime import datetime
from typing import Any, Sequence
from uuid import UUID, uuid4

from motor.motor_asyncio import AsyncIOMotorClientSession

from auditize.database import get_core_db
from auditize.exceptions import (
    UnknownModelException,
    ValidationError,
    enhance_constraint_violation_exception,
)
from auditize.i18n.lang import Lang
from auditize.log.db import LogDatabase, get_log_db_for_config, migrate_log_db
from auditize.log_i18n_profile.models import LogTranslation
from auditize.log_i18n_profile.service import (
    get_log_i18n_profile_translation,
    has_log_i18n_profile,
)
from auditize.permissions.assertions import (
    can_read_logs,
    can_write_logs,
    permissions_and,
)
from auditize.permissions.models import Permissions
from auditize.permissions.operations import is_authorized
from auditize.repo.models import Repo, RepoStats, RepoStatus, RepoUpdate
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    has_resource_document,
    update_resource_document,
)
from auditize.user.models import User


async def _validate_repo(repo: Repo | RepoUpdate):
    if repo.log_i18n_profile_id:
        if not await has_log_i18n_profile(repo.log_i18n_profile_id):
            raise ValidationError(
                f"Log i18n profile {repo.log_i18n_profile_id!r} does not exist"
            )


async def create_repo(repo: Repo, log_db: LogDatabase = None) -> UUID:
    await _validate_repo(repo)
    db = get_core_db()
    repo_id = uuid4()

    async with db.transaction() as session:
        with enhance_constraint_violation_exception("error.constraint_violation.repo"):
            await create_resource_document(
                db.repos,
                {
                    **repo.model_dump(exclude={"id", "log_db_name"}),
                    "log_db_name": (
                        log_db.name if log_db else f"{db.name}_logs_{repo_id}"
                    ),
                },
                resource_id=repo_id,
                session=session,
            )
        if not log_db:
            log_db = await get_log_db_for_config(await _get_repo(repo_id, session))
            await migrate_log_db(log_db)
    return repo_id


async def update_repo(repo_id: UUID, update: RepoUpdate):
    await _validate_repo(update)
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_i18n_profile"
    ):
        await update_resource_document(get_core_db().repos, repo_id, update)


async def _get_repo(repo_id: UUID, session: AsyncIOMotorClientSession = None) -> Repo:
    result = await get_resource_document(get_core_db().repos, repo_id, session=session)
    return Repo.model_validate(result)


async def get_repo(repo_id: UUID | Repo) -> Repo:
    if isinstance(repo_id, Repo):
        return repo_id
    return await _get_repo(repo_id)


async def _get_log_saved_at(log_db: LogDatabase, *, sort: int) -> datetime | None:
    results = (
        await log_db.logs.find({}, projection={"saved_at": 1})
        .sort({"saved_at": sort})
        .limit(1)
        .to_list(None)
    )
    return results[0]["saved_at"] if results else None


async def get_repo_stats(repo_id: UUID) -> RepoStats:
    log_db = await get_log_db_for_config(repo_id)
    stats = RepoStats()

    stats.first_log_date = await _get_log_saved_at(log_db, sort=1)
    stats.last_log_date = await _get_log_saved_at(log_db, sort=-1)
    stats.log_count = await log_db.logs.estimated_document_count()

    db_stats = await log_db.db.command("dbstats")
    stats.storage_size = int(db_stats["storageSize"]) + int(db_stats["indexSize"])

    return stats


async def _get_repos(
    filter: dict[str, Any],
    page: int,
    page_size: int,
) -> tuple[list[Repo], PagePaginationInfo]:
    results, page_info = await find_paginated_by_page(
        get_core_db().repos,
        filter=filter,
        sort=[("name", 1)],
        page=page,
        page_size=page_size,
    )

    return [Repo.model_validate(result) async for result in results], page_info


async def get_repos(
    query: str, page: int, page_size: int
) -> tuple[list[Repo], PagePaginationInfo]:
    return await _get_repos(
        {"$text": {"$search": query}} if query else None, page, page_size
    )


async def get_all_repos():
    results = get_core_db().repos.find({})
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

    return await _get_repos(filter, page, page_size)


async def delete_repo(repo_id: UUID):
    # avoid circular imports
    from auditize.apikey.service import remove_repo_from_apikeys_permissions
    from auditize.log_filter.service import delete_log_filters_with_repo
    from auditize.user.service import remove_repo_from_users_permissions

    log_db = await get_log_db_for_config(repo_id)
    core_db = get_core_db()
    async with core_db.transaction() as session:
        await delete_resource_document(core_db.repos, repo_id, session=session)
        await remove_repo_from_users_permissions(repo_id, session)
        await remove_repo_from_apikeys_permissions(repo_id, session)
        await delete_log_filters_with_repo(repo_id, session)
        await log_db.client.drop_database(log_db.name)


async def is_log_i18n_profile_used_by_repo(profile_id: UUID) -> bool:
    return await has_resource_document(
        get_core_db().repos, {"log_i18n_profile_id": profile_id}
    )


async def get_repo_translation(repo_id: UUID, lang: Lang) -> LogTranslation:
    repo = await get_repo(repo_id)
    if not repo.log_i18n_profile_id:
        return LogTranslation()
    try:
        return await get_log_i18n_profile_translation(repo.log_i18n_profile_id, lang)
    except UnknownModelException:  # NB: this should not happen
        return LogTranslation()


async def ensure_repos_in_permissions_exist(permissions: Permissions):
    for repo_id in permissions.logs.get_repos():
        try:
            await get_repo(repo_id)
        except UnknownModelException:
            raise ValidationError(
                f"Repository {repo_id} cannot be assigned in log permissions as it does not exist"
            )


async def get_retention_period_enabled_repos() -> list[Repo]:
    results = get_core_db().repos.find({"retention_period": {"$ne": None}})
    return [Repo.model_validate(result) async for result in results]
