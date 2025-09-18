from elasticsearch import AsyncElasticsearch

from auditize.config import get_config


def get_elastic_client():
    config = get_config()

    return AsyncElasticsearch(
        config.elastic_url,
        basic_auth=(config.elastic_user, config.elastic_user_password),
        verify_certs=config.elastic_ssl_verify,
        ssl_show_warn=config.elastic_ssl_verify,
    )
