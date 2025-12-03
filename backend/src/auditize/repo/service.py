from typing import Any, Generator, Sequence
from uuid import UUID, uuid4

import elasticsearch
from sqlalchemy import and_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.models.page_pagination import PagePaginationInfo
from auditize.database.dbm import get_dbm
from auditize.database.sql.service import (
    delete_sql_model,
    find_paginated_by_page,
    get_sql_model,
    save_sql_model,
    update_sql_model,
)
from auditize.exceptions import (
    AuditizeException,
    ConstraintViolation,
    NotFoundError,
    ValidationError,
)
from auditize.i18n.lang import Lang
from auditize.log.index import create_index, delete_index
from auditize.log_i18n_profile.models import LogLabels
from auditize.log_i18n_profile.service import get_log_i18n_profile_translation
from auditize.permissions.assertions import (
    can_read_logs_from_all_repos,
    can_write_logs_to_all_repos,
    permissions_and,
)
from auditize.permissions.models import Permissions, RepoLogPermissions
from auditize.permissions.service import is_authorized
from auditize.repo.models import RepoCreate, RepoStats, RepoUpdate
from auditize.repo.sql_models import Repo, RepoStatus
from auditize.user.sql_models import User


def _build_repo_constraint_rules(
    repo: RepoCreate | RepoUpdate,
) -> dict[str, Exception]:
    return {
        "fk_repo_log_i18n_profile_id": ValidationError(
            f"Log i18n profile {str(repo.log_i18n_profile_id)!r} does not exist",
        ),
        "ix_repo_name": ConstraintViolation(
            ("error.constraint_violation.repo", {"name": repo.name}),
        ),
    }


async def create_repo(
    session: AsyncSession, repo_create: RepoCreate, *, existing_log_db_name: str = None
) -> Repo:
    db_name = get_dbm().name
    repo_id = uuid4()
    repo = Repo(
        id=repo_id,
        name=repo_create.name,
        status=repo_create.status,
        retention_period=repo_create.retention_period,
        log_i18n_profile_id=repo_create.log_i18n_profile_id,
        log_db_name=(
            existing_log_db_name
            if existing_log_db_name
            else f"{db_name}_logs_{repo_id}"
        ),
    )
    if not existing_log_db_name:
        await create_index(repo)
    try:
        await save_sql_model(
            session, repo, constraint_rules=_build_repo_constraint_rules(repo_create)
        )
    except (AuditizeException, SQLAlchemyError):
        if not existing_log_db_name:
            await delete_index(repo)
        raise

    return repo


async def update_repo(session: AsyncSession, repo_id: UUID, update: RepoUpdate) -> Repo:
    repo = await get_repo(session, repo_id)
    await update_sql_model(
        session, repo, update, constraint_rules=_build_repo_constraint_rules(update)
    )
    return repo


async def update_repo_reindex_progress(
    session: AsyncSession,
    repo: Repo,
    *,
    reindex_cursor: str | None,
    reindexed_logs_count: int,
) -> None:
    repo.reindex_cursor = reindex_cursor
    repo.reindexed_logs_count = reindexed_logs_count
    await save_sql_model(session, repo)


async def _get_repo(session: AsyncSession, repo_id: UUID) -> Repo:
    return await get_sql_model(session, Repo, repo_id)


async def get_repo(session: AsyncSession, repo: Repo | UUID | str) -> Repo:
    if isinstance(repo, Repo):
        return repo
    repo_id = repo if isinstance(repo, UUID) else UUID(repo)
    return await _get_repo(session, repo_id)


async def get_repo_stats(session: AsyncSession, repo_id: UUID) -> RepoStats:
    from auditize.log.service import LogService

    repo = await _get_repo(session, repo_id)
    log_service = await LogService.for_maintenance(session, repo)
    stats = RepoStats(
        first_log_date=None, last_log_date=None, log_count=0, storage_size=0
    )

    try:
        last_log = await log_service.get_newest_log()
        stats.last_log_date = last_log.saved_at if last_log else None
        stats.log_count = await log_service.get_log_count()
        stats.storage_size = await log_service.get_storage_size()
    except (elasticsearch.NotFoundError, elasticsearch.BadRequestError) as exc:
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


def _filter_repo_by_log_permissions(
    repo_log_permissions: list[RepoLogPermissions],
    has_read_perm: bool,
    has_write_perm: bool,
) -> Generator[UUID, None, None]:
    for repo_perms in repo_log_permissions:
        read_ok = (
            repo_perms.read or repo_perms.readable_entities if has_read_perm else True
        )
        write_ok = repo_perms.write if has_write_perm else True
        if read_ok and write_ok:
            yield repo_perms.repo_id


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

    return list(
        _filter_repo_by_log_permissions(
            user.permissions.repo_log_permissions, has_read_perm, has_write_perm
        )
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
        filter = Repo.status == RepoStatus.ENABLED
    else:
        filter = Repo.status.in_([RepoStatus.ENABLED, RepoStatus.READONLY])

    repo_ids = _get_authorized_repo_ids_for_user(user, user_can_read, user_can_write)
    if repo_ids is not None:
        filter = and_(filter, Repo.id.in_(repo_ids))

    return await _get_repos(session, filter, page, page_size)


async def delete_repo(session: AsyncSession, repo_id: UUID):
    repo = await get_repo(session, repo_id)
    await delete_index(repo)
    await delete_sql_model(session, Repo, repo.id)


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
) -> LogLabels:
    repo = await get_repo(session, repo_id)
    if not repo.log_i18n_profile_id:
        return LogLabels()
    try:
        return await get_log_i18n_profile_translation(
            session, repo.log_i18n_profile_id, lang
        )
    except NotFoundError:  # NB: this should not happen
        return LogLabels()


async def ensure_repos_in_permissions_exist(
    session: AsyncSession, permissions: Permissions
):
    for repo_id in permissions.logs.get_repos():
        try:
            await get_repo(session, repo_id)
        except NotFoundError:
            raise ValidationError(
                f"Repository {repo_id} cannot be assigned in log permissions as it does not exist"
            )


async def get_all_repos(session: AsyncSession) -> list[Repo]:
    return (await session.execute(select(Repo))).scalars().all()


async def get_retention_period_enabled_repos(session: AsyncSession) -> list[Repo]:
    return (
        (await session.execute(select(Repo).where(Repo.retention_period.isnot(None))))
        .scalars()
        .all()
    )
