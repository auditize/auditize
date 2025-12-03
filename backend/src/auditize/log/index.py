import re
import sys
from uuid import UUID

from elasticsearch import AsyncElasticsearch, helpers
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.database import get_elastic_client
from auditize.repo.sql_models import Repo

_MAPPING_VERSION = 2

_TYPE_TEXT_CUSTOM_ASCIIFOLDING = {
    "type": "text",
    "analyzer": "custom_asciifolding",
    "search_analyzer": "custom_asciifolding",
}

_TYPE_CUSTOM_FIELDS = {
    "type": "nested",
    "properties": {
        "type": {"type": "keyword"},
        "name": {"type": "keyword"},
        "value": _TYPE_TEXT_CUSTOM_ASCIIFOLDING,
        "value_enum": {"type": "keyword"},
        "value_boolean": {"type": "boolean"},
        "value_integer": {"type": "long"},
        "value_float": {"type": "double"},
        "value_datetime": {"type": "date"},
    },
}


def _get_log_db_name(repo_or_db_name: Repo | str) -> str:
    return (
        repo_or_db_name.log_db_name
        if isinstance(repo_or_db_name, Repo)
        else repo_or_db_name
    )


def get_read_alias(repo_or_db_name: Repo | str) -> str:
    return _get_log_db_name(repo_or_db_name) + "_read"


def get_write_alias(repo_or_db_name: Repo | str) -> str:
    return _get_log_db_name(repo_or_db_name) + "_write"


def _get_index_name(
    repo_or_db_name: Repo | str, version: int = _MAPPING_VERSION
) -> str:
    return _get_log_db_name(repo_or_db_name) + f"_v{version}"


async def _create_index(
    elastic_client: AsyncElasticsearch, index: str, *, aliases=None
):
    await elastic_client.indices.create(
        index=index,
        aliases=aliases,
        mappings={
            "properties": {
                "log_id": {"type": "keyword"},
                "saved_at": {"type": "date"},
                "action": {
                    "properties": {
                        "type": {"type": "keyword"},
                        "category": {"type": "keyword"},
                    }
                },
                "source": _TYPE_CUSTOM_FIELDS,
                "actor": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            **_TYPE_TEXT_CUSTOM_ASCIIFOLDING,
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "extra": _TYPE_CUSTOM_FIELDS,
                    }
                },
                "resource": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            **_TYPE_TEXT_CUSTOM_ASCIIFOLDING,
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "extra": _TYPE_CUSTOM_FIELDS,
                    }
                },
                "details": _TYPE_CUSTOM_FIELDS,
                "tags": {
                    "type": "nested",
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            **_TYPE_TEXT_CUSTOM_ASCIIFOLDING,
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "attachments": {
                    "type": "nested",
                    "properties": {
                        "name": _TYPE_TEXT_CUSTOM_ASCIIFOLDING,
                        "type": {"type": "keyword"},
                        "mime_type": {"type": "keyword"},
                        "saved_at": {"type": "date"},
                        "data": {"type": "binary"},
                    },
                },
                "entity_path": {
                    "type": "nested",
                    "properties": {
                        "ref": {"type": "keyword"},
                        "name": {
                            **_TYPE_TEXT_CUSTOM_ASCIIFOLDING,
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
            }
        },
        settings={
            "index": {
                "sort.field": ["saved_at", "log_id"],
                "sort.order": ["desc", "desc"],
            },
            "analysis": {
                "analyzer": {
                    "custom_asciifolding": {
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"],
                    }
                }
            },
        },
    )


async def create_index(repo: Repo | str):
    await _create_index(
        elastic_client=get_elastic_client(),
        index=_get_index_name(repo),
        aliases={
            get_read_alias(repo): {"is_write_index": False},
            get_write_alias(repo): {"is_write_index": True},
        },
    )


async def delete_index(repo: Repo):
    elastic_client = get_elastic_client()
    read_index = await _get_alias_index(elastic_client, get_read_alias(repo))
    write_index = await _get_alias_index(elastic_client, get_write_alias(repo))
    await elastic_client.indices.delete(index=write_index)
    if read_index != write_index:
        # we must be in an ongoing or paused reindex operation
        await elastic_client.indices.delete(index=read_index)


async def _get_alias_index(elastic_client: AsyncElasticsearch, alias: str) -> str:
    resp = await elastic_client.indices.get_alias(index=alias)
    return list(resp.keys())[0]


async def _get_index_mapping_version(index: str) -> int:
    match = re.search(r"_v(\d+)$", index)
    return int(match.group(1)) if match else 1


async def _copy_logs(session: AsyncSession, repo: Repo, *, target_index: str):
    from auditize.log.service import LogService
    from auditize.repo.service import update_repo_reindex_progress

    log_service = await LogService.for_maintenance(session, repo)
    total_logs = await log_service.get_log_count()
    copied_logs = repo.reindexed_logs_count
    pagination_cursor = repo.reindex_cursor
    while True:
        logs, next_cursor = await log_service.get_logs(
            limit=100, pagination_cursor=pagination_cursor
        )
        await helpers.async_bulk(
            log_service.es,
            [
                {
                    "_index": target_index,
                    "_id": log.id,
                    "_source": log.model_dump(context="es"),
                }
                for log in logs
            ],
        )
        copied_logs += len(logs)
        print(f"Copied {copied_logs} logs out of {total_logs}\r", end="")
        sys.stdout.flush()
        await update_repo_reindex_progress(
            session,
            repo,
            reindex_cursor=next_cursor,
            reindexed_logs_count=copied_logs if next_cursor else 0,
        )
        if not next_cursor:
            break
        pagination_cursor = next_cursor


async def _prepare_reindex(
    repo: Repo,
    current_write_index: str,
    target_write_index: str,
    write_alias: str,
):
    """
    Creates a new index and switches the write alias to point to it.
    """

    elastic_client = get_elastic_client()

    await _create_index(elastic_client, target_write_index)
    await elastic_client.indices.update_aliases(
        actions=[
            {
                "remove": {
                    "alias": write_alias,
                    "index": current_write_index,
                }
            },
            {
                "add": {
                    "alias": write_alias,
                    "index": target_write_index,
                    "is_write_index": True,
                },
            },
        ]
    )
    print(f"Created new index {target_write_index} for repository {repo.id}")


async def _finalize_reindex(repo: Repo):
    """
    Completes the reindex operation by:
    - pointing the read alias to the newly created index,
    - deleting the former index.
    """

    elastic_client = get_elastic_client()

    read_alias = get_read_alias(repo)
    current_read_index = await _get_alias_index(elastic_client, read_alias)
    current_write_index = await _get_alias_index(elastic_client, get_write_alias(repo))

    ###
    # Point the read alias to the newly created index
    ###
    await elastic_client.indices.update_aliases(
        actions=[
            {
                "remove": {
                    "alias": read_alias,
                    "index": current_read_index,
                }
            },
            {
                "add": {
                    "alias": read_alias,
                    "index": current_write_index,
                    "is_write_index": False,
                },
            },
        ]
    )

    ###
    # Delete the former index
    ###
    await elastic_client.indices.delete(index=current_read_index)

    print(f"Reindex operation for repository {repo.id} completed")


async def is_index_up_to_date(
    repo: Repo, *, target_version: int = _MAPPING_VERSION
) -> bool:
    elastic_client = get_elastic_client()

    read_alias = get_read_alias(repo)
    write_alias = get_write_alias(repo)
    current_read_index = await _get_alias_index(elastic_client, read_alias)
    current_write_index = await _get_alias_index(elastic_client, write_alias)
    current_write_version = await _get_index_mapping_version(current_write_index)

    is_reindex_in_progress = current_write_index != current_read_index
    return current_write_version >= target_version and not is_reindex_in_progress


async def get_reindexable_repos(session: AsyncSession) -> list[Repo]:
    from auditize.repo.service import get_all_repos

    return [
        repo
        for repo in await get_all_repos(session)
        if not await is_index_up_to_date(repo)
    ]


async def reindex_index(
    session: AsyncSession,
    repo: Repo | str | UUID,
    *,
    target_version: int = _MAPPING_VERSION,
) -> str | None:
    """
    Reindexes the Elasticsearch log index to a new version by:
    - creating a new index with the desired mapping,
    - updating the write alias to point to it,
    - copying data from the old index to the new index,
    - point the read alias to the new index,
    - delete the old index.

    Please note that:
    - the read alias is not updated, so the old index is still available for reading.
      It means that logs written during the reindex operation are not yet visible.
    """
    from auditize.repo.service import get_repo

    ###
    # Check if the index is already at the target version or if the reindex is already in progress.
    ###
    elastic_client = get_elastic_client()

    repo = await get_repo(session, repo)

    read_alias = get_read_alias(repo)
    write_alias = get_write_alias(repo)
    current_read_index = await _get_alias_index(elastic_client, read_alias)
    current_write_index = await _get_alias_index(elastic_client, write_alias)
    is_reindex_in_progress = current_write_index != current_read_index

    if await is_index_up_to_date(repo, target_version=target_version):
        print(f"Repository {repo.id} index is already at version {target_version}")
        return

    target_write_index = _get_index_name(repo, target_version)

    if is_reindex_in_progress:
        print(f"Resuming reindex operation for repository {repo.id}")
    else:
        await _prepare_reindex(
            repo, current_write_index, target_write_index, write_alias
        )

    ###
    # Reindex the data from the former index to the newly created index
    ###
    print(f"Reindexing data from index {current_read_index} to {target_write_index}")
    await _copy_logs(session, repo, target_index=target_write_index)

    ###
    # Finalize the reindex operation
    ###
    await _finalize_reindex(repo)
