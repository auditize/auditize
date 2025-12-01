from elasticsearch import AsyncElasticsearch

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


async def create_index(elastic_client: AsyncElasticsearch, index_name: str):
    await elastic_client.indices.create(
        index=index_name,
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
