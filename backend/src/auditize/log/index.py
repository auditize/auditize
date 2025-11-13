import re
import warnings

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import GeneralAvailabilityWarning

from auditize.database import get_elastic_client
from auditize.repo.sql_models import Repo

_MAPPING_VERSION = 2

_TYPE_SIMPLE_ANALYZER = {
    "type": "text",
    "analyzer": "simple",
    "search_analyzer": "simple",
}

_TYPE_CUSTOM_FIELDS = {
    "type": "nested",
    "properties": {
        "name": {"type": "keyword"},
        "value": _TYPE_SIMPLE_ANALYZER,
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
                            **_TYPE_SIMPLE_ANALYZER,
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
                            **_TYPE_SIMPLE_ANALYZER,
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
                            **_TYPE_SIMPLE_ANALYZER,
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "attachments": {
                    "type": "nested",
                    "properties": {
                        "name": _TYPE_SIMPLE_ANALYZER,
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
                            **_TYPE_SIMPLE_ANALYZER,
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
    await elastic_client.indices.delete(index=_get_index_name(repo))


async def _get_alias_index(elastic_client: AsyncElasticsearch, alias: str) -> str:
    resp = await elastic_client.indices.get_alias(index=alias)
    return list(resp.keys())[0]


async def _get_index_mapping_version(index: str) -> int:
    match = re.search(r"_v(\d+)$", index)
    return int(match.group(1)) if match else 1


async def reindex_index(repo: Repo, *, target_version: int | None = None) -> str | None:
    """
    Reindexes the Elasticsearch log index to a new version by:
    - creating a new index with the desired mapping,
    - updating the write alias to point to it,
    - copying data from the old index using Elasticsearch's reindex API,

    Please note that:
    - the read alias is not updated, so the old index is still available for reading;
      it means that logs written during the reindex operation are not yet visible,
    - the process must be completed by calling `complete_reindex()`.

    Returns the task ID of the reindex operation or None if the index is
    already at the target version.
    """
    ###
    # Check if the index is already at the target version
    ###
    if target_version is None:
        target_version = _MAPPING_VERSION

    elastic_client = get_elastic_client()

    write_alias = get_write_alias(repo)
    current_write_index = await _get_alias_index(elastic_client, write_alias)

    current_version = await _get_index_mapping_version(current_write_index)

    if current_version >= target_version:
        print(f"Repository {repo.id} index is already at version {target_version}")
        return None

    ###
    # Create the new index
    ###
    target_write_index = _get_index_name(repo, target_version)
    await _create_index(elastic_client, target_write_index)

    ###
    # Point the write alias to the newly created index
    ###
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

    ###
    # Reindex the data from the current write index to the newly created index
    ###
    resp = await elastic_client.reindex(
        source={"index": [current_write_index]},
        dest={"index": target_write_index},
        wait_for_completion=False,
    )
    return resp["task"]


async def get_reindex_status(task_id: str):
    """
    Return the result of /_tasks/{task_id}
    """
    # NB: the API seems stable enough and the reindex operation is under test
    # on our side
    elastic_client = get_elastic_client()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=GeneralAvailabilityWarning)
        return await elastic_client.tasks.get(task_id=task_id)


async def complete_reindex(repo: Repo):
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
