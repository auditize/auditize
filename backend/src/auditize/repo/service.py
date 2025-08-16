from typing import Any, Sequence
from uuid import UUID, uuid4

import elasticsearch
from motor.motor_asyncio import AsyncIOMotorClientSession
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database import get_core_db
from auditize.exceptions import (
    UnknownModelException,
    ValidationError,
    enhance_constraint_violation_exception,
)
from auditize.i18n.lang import Lang
from auditize.log_i18n_profile.models import LogTranslation
from auditize.log_i18n_profile.service import (
    get_log_i18n_profile_translation,
    has_log_i18n_profile,
)
from auditize.permissions.assertions import (
    can_read_logs_from_all_repos,
    can_write_logs_to_all_repos,
    permissions_and,
)
from auditize.permissions.models import Permissions, PermissionsInput
from auditize.permissions.operations import is_authorized
from auditize.repo.models import Repo, RepoCreate, RepoStats, RepoStatus, RepoUpdate
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.sql_service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document2,
    delete_resource_document,
    get_resource_document,
    has_resource_document,
    update_resource_document,
)
from auditize.resource.sql_service import (
    delete_sql_model,
    get_sql_model,
    save_sql_model,
    update_sql_model,
)
from auditize.user.models import User


async def _validate_repo(session: AsyncSession, repo: RepoCreate | RepoUpdate):
    if repo.log_i18n_profile_id:
        if not await has_log_i18n_profile(session, repo.log_i18n_profile_id):
            raise ValidationError(
                f"Log i18n profile {repo.log_i18n_profile_id!r} does not exist"
            )


async def create_repo(
    session: AsyncSession, repo_create: RepoCreate, log_db_name: str = None
) -> Repo:
    from auditize.log.service import LogService

    await _validate_repo(session, repo_create)
    db = get_core_db()
    repo_id = uuid4()

    with enhance_constraint_violation_exception("error.constraint_violation.repo"):
        repo = Repo(
            id=repo_id,
            name=repo_create.name,
            status=repo_create.status,
            retention_period=repo_create.retention_period,
            log_i18n_profile_id=repo_create.log_i18n_profile_id,
            log_db_name=(log_db_name if log_db_name else f"{db.name}_logs_{repo_id}"),
        )
        await save_sql_model(session, repo)

    if not log_db_name:
        log_service = await LogService.for_maintenance(session, repo)
        await log_service.create_log_db()
    return repo


async def update_repo(session: AsyncSession, repo_id: UUID, update: RepoUpdate) -> Repo:
    await _validate_repo(session, update)
    with enhance_constraint_violation_exception(
        "error.constraint_violation.log_i18n_profile"
    ):
        repo = await get_repo(session, repo_id)
        await update_sql_model(session, repo, update)
    return repo


async def _get_repo(session: AsyncSession, repo_id: UUID) -> Repo:
    return await get_sql_model(session, Repo, repo_id)


async def get_repo(session: AsyncSession, repo_id: UUID | Repo) -> Repo:
    if isinstance(repo_id, Repo):
        return repo_id
    return await _get_repo(session, repo_id)


async def get_repo_stats(session: AsyncSession, repo_id: UUID) -> RepoStats:
    from auditize.log.service import LogService

    repo = await _get_repo(session, repo_id)
    log_service = await LogService.for_maintenance(session, repo)
    stats = RepoStats()

    try:
        first_log = await log_service.get_oldest_log()
        last_log = await log_service.get_newest_log()
        stats.first_log_date = first_log.saved_at if first_log else None
        stats.last_log_date = last_log.saved_at if last_log else None
        stats.log_count = await log_service.get_log_count()
        stats.storage_size = await log_service.get_storage_size()
    except (elasticsearch.NotFoundError, elasticsearch.BadRequestError) as exc:
        # FIXME: handle the case where the log db is a MongoDB database
        print(f"Got an error while fetching stats for repo {repo_id}: {exc}")
        pass

    return stats


async def _get_repos(
    session: AsyncSession,
    filter: Any | None,
    page: int,
    page_size: int,
) -> tuple[list[Repo], PagePaginationInfo]:
    models, page_info = await find_paginated_by_page(
        session,
        Repo,
        filter=filter,
        order_by=Repo.name.asc(),
        page=page,
        page_size=page_size,
    )
    return models, page_info


async def get_repos(
    session: AsyncSession, query: str, page: int, page_size: int
) -> tuple[list[Repo], PagePaginationInfo]:
    return await _get_repos(
        session, Repo.name.ilike(f"%{query}%") if query else None, page, page_size
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
                user.permissions,
                permissions_and(
                    can_read_logs_from_all_repos(), can_write_logs_to_all_repos()
                ),
            ),
            (
                is_authorized(user.permissions, can_read_logs_from_all_repos())
                and (has_read_perm and not has_write_perm)
            ),
            (
                is_authorized(user.permissions, can_write_logs_to_all_repos())
                and (has_write_perm and not has_read_perm)
            ),
        )
    )
    if no_filtering_needed:
        return None

    return user.permissions.logs.get_repos(
        can_read=(
            has_read_perm
            and not is_authorized(user.permissions, can_read_logs_from_all_repos())
        ),
        can_write=(
            has_write_perm
            and not is_authorized(user.permissions, can_write_logs_to_all_repos())
        ),
    )


async def get_user_repos(
    session: AsyncSession,
    *,
    user: User,
    user_can_read: bool,
    user_can_write: bool,
    page: int,
    page_size: int,
) -> tuple[list[Repo], PagePaginationInfo]:
    if user_can_write:
        filter = Repo.status == RepoStatus.enabled
    else:
        filter = Repo.status.in_([RepoStatus.enabled, RepoStatus.readonly])

    repo_ids = _get_authorized_repo_ids_for_user(user, user_can_read, user_can_write)
    if repo_ids is not None:
        filter = and_(filter, Repo.id.in_(repo_ids))

    return await _get_repos(session, filter, page, page_size)


async def delete_repo(session: AsyncSession, repo_id: UUID):
    # avoid circular imports
    from auditize.apikey.service import remove_repo_from_apikeys_permissions
    from auditize.log.service import LogService
    from auditize.log_filter.service import delete_log_filters_with_repo
    from auditize.user.service import remove_repo_from_users_permissions

    core_db = get_core_db()
    async with core_db.transaction() as mongo_session:
        log_service = await LogService.for_maintenance(session, repo_id)
        await delete_sql_model(session, Repo, repo_id)
        await remove_repo_from_users_permissions(repo_id, mongo_session)
        await remove_repo_from_apikeys_permissions(repo_id, mongo_session)
        await delete_log_filters_with_repo(session, repo_id)
        await log_service.delete_log_db()


async def is_log_i18n_profile_used_by_repo(
    session: AsyncSession, profile_id: UUID
) -> bool:
    return (
        await session.execute(
            select(Repo).where(Repo.log_i18n_profile_id == profile_id)
        )
    ).scalars().first() is not None


async def get_repo_translation(
    session: AsyncSession, repo_id: UUID, lang: Lang
) -> LogTranslation:
    repo = await get_repo(session, repo_id)
    if not repo.log_i18n_profile_id:
        return LogTranslation()
    try:
        return await get_log_i18n_profile_translation(
            session, repo.log_i18n_profile_id, lang
        )
    except UnknownModelException:  # NB: this should not happen
        return LogTranslation()


async def ensure_repos_in_permissions_exist(
    session: AsyncSession, permissions: Permissions
):
    for repo_id in permissions.logs.get_repos():
        try:
            await get_repo(session, repo_id)
        except UnknownModelException:
            raise ValidationError(
                f"Repository {repo_id} cannot be assigned in log permissions as it does not exist"
            )


async def get_retention_period_enabled_repos(session: AsyncSession) -> list[Repo]:
    return (
        (await session.execute(select(Repo).where(Repo.retention_period.isnot(None))))
        .scalars()
        .all()
    )
