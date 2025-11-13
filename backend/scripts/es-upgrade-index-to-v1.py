#!/usr/bin/env python3

"""
Upgrade `auditize_logs_*` indices to v1 (custom preparation step for v2 migration).
Ensure `auditize_logs_*` indices expose the expected read/write aliases.
"""

import logging

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

from auditize.config import init_config

INDEX_PREFIX = "auditize_logs_"
READ_ALIAS_SUFFIX = "_read"
WRITE_ALIAS_SUFFIX = "_write"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def get_elasticsearch_client() -> Elasticsearch:
    config = init_config()

    return Elasticsearch(
        config.elastic_url,
        basic_auth=(
            (config.elastic_user, config.elastic_password)
            if config.elastic_user
            else None
        ),
        verify_certs=config.elastic_ssl_verify,
        ssl_show_warn=config.elastic_ssl_verify,
    )


def list_target_indices(client: Elasticsearch) -> list[str]:
    try:
        indices = client.indices.get(index=f"{INDEX_PREFIX}*")
    except NotFoundError:
        return []

    return sorted(name for name in indices if name.startswith(INDEX_PREFIX))


def remove_existing_aliases(client: Elasticsearch, index_name: str) -> None:
    try:
        alias_data = client.indices.get_alias(index=index_name)
    except NotFoundError:
        return

    aliases = alias_data.get(index_name, {}).get("aliases", {})
    if not aliases:
        return

    actions = [{"remove": {"index": index_name, "alias": alias}} for alias in aliases]
    client.indices.update_aliases(body={"actions": actions})


def get_base_alias_name(index_name: str) -> str:
    if index_name.endswith("_v1"):
        return index_name.rsplit("_v1", 1)[0]
    return index_name


def create_expected_aliases(client: Elasticsearch, index_name: str) -> None:
    base_name = get_base_alias_name(index_name)

    actions = [
        {
            "add": {
                "index": index_name,
                "alias": f"{base_name}{READ_ALIAS_SUFFIX}",
                "is_write_index": False,
            }
        },
        {
            "add": {
                "index": index_name,
                "alias": f"{base_name}{WRITE_ALIAS_SUFFIX}",
                "is_write_index": True,
            }
        },
    ]

    client.indices.update_aliases(body={"actions": actions})


def process_index(client: Elasticsearch, index_name: str) -> None:
    logger.info("Processing %s", index_name)
    remove_existing_aliases(client, index_name)
    create_expected_aliases(client, index_name)
    logger.info("Updated aliases for %s", index_name)


def main() -> None:
    client = get_elasticsearch_client()

    try:
        indices = list_target_indices(client)
        if not indices:
            logger.info("No indices found matching %s*", INDEX_PREFIX)
            return

        for index_name in indices:
            process_index(client, index_name)
    finally:
        client.close()


if __name__ == "__main__":
    main()
