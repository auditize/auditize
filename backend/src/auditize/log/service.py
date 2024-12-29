import base64
import json
import uuid
from datetime import datetime, timedelta
from functools import partialmethod
from typing import Self
from uuid import UUID

import elasticsearch
from aiocache import Cache
from elasticsearch import AsyncElasticsearch

from auditize.config import get_config
from auditize.database import DatabaseManager
from auditize.exceptions import (
    ConstraintViolation,
    InvalidPaginationCursor,
    PermissionDenied,
    UnknownModelException,
)
from auditize.helpers.datetime import now, serialize_datetime
from auditize.log.models import Entity, Log, LogSearchParams
from auditize.repo.models import Repo, RepoStatus
from auditize.repo.service import get_repo, get_retention_period_enabled_repos
from auditize.resource.pagination.cursor.serialization import (
    load_pagination_cursor,
    serialize_pagination_cursor,
)
from auditize.resource.service import (
    has_resource_document,
)

# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}

_CONSOLIDATED_LOG_ENTITIES = Cache(Cache.MEMORY)


class _LogsPaginationCursor:
    def __init__(self, date: datetime, id: uuid.UUID):
        self.date = date
        self.id = id

    @classmethod
    def load(cls, value: str) -> Self:
        decoded = load_pagination_cursor(value)

        try:
            return cls(
                datetime.fromisoformat(decoded["date"]), uuid.UUID(decoded["id"])
            )
        except (KeyError, ValueError):
            raise InvalidPaginationCursor(value)

    def serialize(self) -> str:
        return serialize_pagination_cursor(
            {
                "date": serialize_datetime(self.date, with_milliseconds=True),
                "id": str(self.id),
            }
        )


class _OffsetPaginationCursor:
    def __init__(self, offset: int):
        self.offset = offset

    @classmethod
    def load(cls, value: str | None) -> Self:
        if value is not None:
            decoded = load_pagination_cursor(value)
            try:
                return cls(int(decoded["offset"]))
            except (KeyError, ValueError):
                raise InvalidPaginationCursor(value)
        else:
            return cls(offset=0)

    def serialize(self) -> str:
        return serialize_pagination_cursor({"offset": self.offset})

    def get_next_cursor(self, results: list, limit: int) -> str | None:
        # we previously fetched one extra result to check if there are more results to fetch
        if len(results) == limit + 1:
            next_cursor_obj = _OffsetPaginationCursor(self.offset + limit)
            next_cursor = next_cursor_obj.serialize()
            results.pop(-1)  # remove the extra log
        else:
            next_cursor = None
        return next_cursor


class LogService:
    def __init__(self, repo: Repo, es: AsyncElasticsearch):
        self.repo = repo
        self.es = es
        self.index = repo.log_db_name
        self._refresh = get_config().test_mode

    @classmethod
    async def _for_statuses(
        cls, repo: Repo | UUID, statuses: list[RepoStatus] = None
    ) -> Self:
        from auditize.repo.service import get_repo  # avoid circular import

        if isinstance(repo, UUID):
            repo = await get_repo(repo)

        if statuses:
            if repo.status not in statuses:
                # NB: we could also raise a ConstraintViolation, to be discussed
                raise PermissionDenied(
                    "The repository status does not allow the requested operation"
                )

        return cls(repo, DatabaseManager.get().elastic_client)

    @classmethod
    async def for_reading(cls, repo: Repo | UUID):
        return await cls._for_statuses(repo, [RepoStatus.enabled, RepoStatus.readonly])

    @classmethod
    async def for_writing(cls, repo: Repo | UUID):
        return await cls._for_statuses(repo, [RepoStatus.enabled])

    @classmethod
    async def for_config(cls, repo: Repo | UUID):
        return await cls._for_statuses(repo)

    for_maintenance = for_config

    async def check_log(self, log: Log):
        raise NotImplementedError()
        parent_entity_ref = None
        for entity in log.entity_path:
            if await has_resource_document(
                self.log_db.log_entities,
                {
                    "parent_entity_ref": parent_entity_ref,
                    "name": entity.name,
                    "ref": {"$ne": entity.ref},
                },
            ):
                raise ConstraintViolation(
                    f"Entity {entity.ref!r} is invalid, there are other logs with "
                    f"the same entity name but with another ref at the same level (same parent)"
                )
            parent_entity_ref = entity.ref

    async def save_log(self, log: Log) -> UUID:
        # await self.check_log(log)

        log_id = uuid.uuid4()
        await self.es.index(
            index=self.index,
            id=str(log_id),
            document={
                "log_id": log_id,
                "saved_at": serialize_datetime(log.saved_at, with_milliseconds=True),
                **log.model_dump(exclude={"id"}),
            },
            refresh=self._refresh,
        )
        await self._consolidate_log_entity_path(log.entity_path)

        return log_id

    async def save_log_attachment(self, log_id: UUID, attachment: Log.Attachment):
        resp = await self.es.update_by_query(
            index=self.index,
            query=self._log_query(log_id),
            script={
                "source": "ctx._source.attachments.add(params.attachment)",
                "params": {
                    "attachment": {
                        **attachment.model_dump(exclude={"data"}),
                        "data": base64.b64encode(attachment.data).decode(),
                    }
                },
            },
            refresh=self._refresh,
        )
        if resp["updated"] == 0:
            raise UnknownModelException()

    @staticmethod
    def _authorized_entity_filter(authorized_entities: set[str]):
        return {
            "nested": {
                "path": "entity_path",
                "query": {
                    "bool": {
                        "filter": {
                            "terms": {"entity_path.ref": list(authorized_entities)}
                        }
                    }
                },
            }
        }

    @staticmethod
    def _log_query(log_id: UUID, authorized_entities: set[str] = None):
        query: dict = {"bool": {"filter": [{"term": {"_id": str(log_id)}}]}}
        if authorized_entities:
            query["bool"]["filter"].append(
                LogService._authorized_entity_filter(authorized_entities)
            )
        return query

    async def get_log(self, log_id: UUID, authorized_entities: set[str]) -> Log:
        print(
            "LOG QUERY: %s" % json.dumps(self._log_query(log_id, authorized_entities))
        )
        resp = await self.es.search(
            index=self.index,
            query=self._log_query(log_id, authorized_entities),
            source_excludes=["attachments.data"],
        )
        documents = resp["hits"]["hits"]
        if not documents:
            raise UnknownModelException()

        model = Log.model_validate({**documents[0]["_source"], "_id": log_id})
        return model

    async def get_log_attachment(
        self, log_id: UUID, attachment_idx: int, authorized_entities: set[str]
    ) -> Log.Attachment:
        # NB: we retrieve all attachments here, which is not really efficient is the log contains
        # more than 1 log, unfortunately ES does not a let us retrieve a nested object to a specific
        # array index unless adding an extra metadata such as "index" to the stored document
        resp = await self.es.search(
            index=self.index,
            query=self._log_query(log_id, authorized_entities),
            source_includes=["attachments"],
        )

        try:
            attachment = resp["hits"]["hits"][0]["_source"]["attachments"][
                attachment_idx
            ]
        except IndexError:
            raise UnknownModelException()

        return Log.Attachment.model_validate(
            {**attachment, "data": base64.b64decode(attachment["data"])}
        )

    @staticmethod
    def _custom_field_search_filter(type: str, fields: dict[str, str]):
        return [
            {
                "nested": {
                    "path": type,
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {f"{type}.name": name}},
                                {"term": {f"{type}.value.keyword": value}},
                            ]
                        }
                    },
                }
            }
            for name, value in fields.items()
        ]

    @staticmethod
    def _nested_filter_term(path, name, value):
        return {
            "nested": {
                "path": path,
                "query": {"bool": {"filter": [{"term": {name: value}}]}},
            }
        }

    @classmethod
    def _prepare_es_query(
        cls,
        search_params: LogSearchParams,
    ) -> list[dict]:
        sp = search_params
        filter = []
        if sp.action_type:
            filter.append({"term": {"action.type": sp.action_type}})
        if sp.action_category:
            filter.append({"term": {"action.category": sp.action_category}})
        if sp.source:
            filter.extend(cls._custom_field_search_filter("source", sp.source))
        if sp.actor_type:
            filter.append({"term": {"actor.type": sp.actor_type}})
        if sp.actor_name:
            filter.append({"term": {"actor.name.keyword": sp.actor_name}})
        if sp.actor_ref:
            filter.append({"term": {"actor.ref": sp.actor_ref}})
        if sp.actor_extra:
            filter.extend(
                cls._custom_field_search_filter("actor.extra", sp.actor_extra)
            )
        if sp.resource_type:
            filter.append({"term": {"resource.type": sp.resource_type}})
        if sp.resource_name:
            filter.append({"term": {"resource.name.keyword": sp.resource_name}})
        if sp.resource_ref:
            filter.append({"term": {"resource.ref": sp.resource_ref}})
        if sp.resource_extra:
            filter.extend(
                cls._custom_field_search_filter("resource.extra", sp.resource_extra)
            )
        if sp.details:
            filter.extend(cls._custom_field_search_filter("details", sp.details))
        if sp.tag_ref:
            filter.append(cls._nested_filter_term("tags", "tags.ref", sp.tag_ref))
        if sp.tag_type:
            filter.append(cls._nested_filter_term("tags", "tags.type", sp.tag_type))
        if sp.tag_name:
            filter.append(
                cls._nested_filter_term("tags", "tags.name.keyword", sp.tag_name)
            )
        if sp.has_attachment is not None:
            if sp.has_attachment:
                filter.append(
                    {
                        "nested": {
                            "path": "attachments",
                            "query": {"exists": {"field": "attachments"}},
                        }
                    }
                )
            else:
                filter.append(
                    {
                        "bool": {
                            "must_not": {
                                "nested": {
                                    "path": "attachments",
                                    "query": {"exists": {"field": "attachments"}},
                                }
                            }
                        }
                    }
                )

        if sp.attachment_name:
            filter.append(
                cls._nested_filter_term(
                    "attachments", "attachments.name.keyword", sp.attachment_name
                )
            )
        if sp.attachment_type:
            filter.append(
                cls._nested_filter_term(
                    "attachments", "attachments.type", sp.attachment_type
                )
            )
        if sp.attachment_mime_type:
            filter.append(
                cls._nested_filter_term(
                    "attachments", "attachments.mime_type", sp.attachment_mime_type
                )
            )
        if sp.entity_ref:
            filter.append(
                cls._nested_filter_term("entity_path", "entity_path.ref", sp.entity_ref)
            )
        if sp.since:
            filter.append({"range": {"saved_at": {"gte": sp.since}}})
        if sp.until:
            # don't want to miss logs saved at the same second, meaning that the "until: ...23:59:59" criterion
            # will also include logs saved at 23:59:59.500 for instance
            filter.append(
                {"range": {"saved_at": {"lte": sp.until.replace(microsecond=999999)}}}
            )
        return filter

    async def get_logs(
        self,
        *,
        authorized_entities: set[str] = None,
        search_params: LogSearchParams = None,
        limit: int = 10,
        pagination_cursor: str = None,
    ) -> tuple[list[Log], str | None]:
        filter = self._prepare_es_query(search_params)

        if authorized_entities:
            filter.append(self._authorized_entity_filter(authorized_entities))

        search_after = (
            load_pagination_cursor(pagination_cursor) if pagination_cursor else None
        )

        query = {"bool": {"filter": filter}}
        print("QUERY: %s" % json.dumps(query, default=str))
        resp = await self.es.search(
            index=self.index,
            query=query,
            search_after=search_after,
            source_excludes=["attachments.data"],
            sort=[{"saved_at": "desc", "log_id": "desc"}],
            size=limit + 1,
            track_total_hits=False,
        )
        print("RESPONSE: %s" % json.dumps(dict(resp), default=str))
        hits = list(resp["hits"]["hits"])

        # we previously fetched one extra log to check if there are more logs to fetch
        if len(hits) == limit + 1:
            # there is still more logs to fetch, so we need to return a next_cursor based on the last log WITHIN the
            # limit range
            next_cursor = serialize_pagination_cursor(hits[-2]["sort"])
            hits.pop(-1)
        else:
            next_cursor = None

        logs = [
            Log.model_validate({**hit["_source"], "_id": hit["_id"]}) for hit in hits
        ]

        return logs, next_cursor

    async def _get_sorted_log(self, sort) -> Log | None:
        resp = await self.es.search(
            index=self.index,
            query={"match_all": {}},
            sort=sort,
            size=1,
        )
        hits = resp["hits"]["hits"]
        if not hits:
            return None
        return Log.model_validate({**hits[0]["_source"], "_id": hits[0]["_id"]})

    async def get_oldest_log(self) -> Log | None:
        return await self._get_sorted_log([{"saved_at": "asc", "log_id": "asc"}])

    async def get_newest_log(self) -> Log | None:
        return await self._get_sorted_log([{"saved_at": "desc", "log_id": "desc"}])

    async def get_log_count(self) -> int:
        resp = await self.es.count(
            index=self.index,
            query={"match_all": {}},
        )
        return resp["count"]

    async def get_storage_size(self) -> int:
        resp = await self.es.indices.stats(index=self.index)
        return resp["_all"]["primaries"]["store"]["size_in_bytes"]

    async def _get_paginated_agg(
        self,
        *,
        nested: str = None,
        field: str,
        query: dict = None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[str], str]:
        after = load_pagination_cursor(pagination_cursor) if pagination_cursor else None

        aggregations = {
            "group_by": {
                "composite": {
                    "size": limit,
                    "sources": [{field: {"terms": {"field": field, "order": "asc"}}}],
                    **({"after": after} if after else {}),
                }
            },
        }
        if nested:
            aggregations = {
                "nested_group_by": {
                    "nested": {
                        "path": nested,
                    },
                    "aggs": aggregations,
                },
            }

        print("REQUEST: %s" % json.dumps(aggregations))
        resp = await self.es.search(
            index=self.index,
            query=query,
            aggregations=aggregations,
            size=0,
        )

        print("RESPONSE: %s" % json.dumps(dict(resp)))

        if nested:
            group_by_result = resp["aggregations"]["nested_group_by"]["group_by"]
        else:
            group_by_result = resp["aggregations"]["group_by"]

        if len(group_by_result["buckets"]) == limit and "after_key" in group_by_result:
            next_cursor = serialize_pagination_cursor(group_by_result["after_key"])
        else:
            next_cursor = None

        values = [bucket["key"][field] for bucket in group_by_result["buckets"]]

        return values, next_cursor

    get_log_action_categories = partialmethod(
        _get_paginated_agg, field="action.category"
    )

    async def get_log_action_types(
        self,
        action_category: str | None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[str], str]:
        return await self._get_paginated_agg(
            field="action.type",
            query=(
                {"bool": {"filter": {"term": {"action.category": action_category}}}}
                if action_category
                else None
            ),
            limit=limit,
            pagination_cursor=pagination_cursor,
        )

    get_log_tag_types = partialmethod(
        _get_paginated_agg, nested="tags", field="tags.type"
    )

    get_log_actor_types = partialmethod(_get_paginated_agg, field="actor.type")

    get_log_actor_extra_fields = partialmethod(
        _get_paginated_agg, nested="actor.extra", field="actor.extra.name"
    )

    get_log_resource_types = partialmethod(_get_paginated_agg, field="resource.type")

    get_log_resource_extra_fields = partialmethod(
        _get_paginated_agg, nested="resource.extra", field="resource.extra.name"
    )

    get_log_source_fields = partialmethod(
        _get_paginated_agg, nested="source", field="source.name"
    )

    get_log_detail_fields = partialmethod(
        _get_paginated_agg, nested="details", field="details.name"
    )

    get_log_attachment_types = partialmethod(
        _get_paginated_agg, nested="attachments", field="attachments.type"
    )

    get_log_attachment_mime_types = partialmethod(
        _get_paginated_agg, nested="attachments", field="attachments.mime_type"
    )

    async def _apply_log_retention_period(self):
        if not self.repo.retention_period:
            return

        resp = await self.es.delete_by_query(
            index=self.index,
            query={
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "saved_at": {
                                    "lt": now()
                                    - timedelta(days=self.repo.retention_period)
                                }
                            }
                        }
                    ]
                }
            },
            refresh=self._refresh,
        )
        print("RESPONSE: %s" % json.dumps(dict(resp)))
        if resp["deleted"] > 0:
            print(
                f"Deleted {resp["deleted"]} logs older than {self.repo.retention_period} days "
                f"in log repository {self.repo.name!r}"
            )

    @classmethod
    async def apply_log_retention_period(cls, repo: UUID | Repo = None):
        if repo:
            repos = [await get_repo(repo)]
        else:
            repos = await get_retention_period_enabled_repos()

        for repo in repos:
            service = await cls.for_maintenance(repo)
            await service._apply_log_retention_period()
            # FIXME: we should also delete the consolidated entities that are not referenced by any log

    async def _consolidate_log_entity(
        self, entity: Log.Entity, parent_entity: Log.Entity | None
    ):
        doc = {
            "ref": entity.ref,
            "name": entity.name,
            "parent_entity_ref": parent_entity.ref if parent_entity else None,
        }
        cache_key = "%s:%s" % (self.index, doc.values())
        if await _CONSOLIDATED_LOG_ENTITIES.exists(cache_key):
            return

        try:
            print("CONSOLIDATE ENTITY: %s" % json.dumps(doc))
            await self.es.update(
                index=f"{self.index}_entities",
                id=str(uuid.uuid4()),
                doc=doc,
                doc_as_upsert=True,
                refresh=self._refresh,
            )
        except elasticsearch.ConflictError:
            # We may encounter a 409 error if two updates are made at the same time
            # just ignore those errors and mark the log entity as already consolidated.
            # It assumes that the being log entity being updated was the same as the one
            # we attempted to index.
            print(
                f"Detected conflict error while consolidating entity {entity.ref}, skip it."
            )
        await _CONSOLIDATED_LOG_ENTITIES.set(cache_key, True)

    async def _consolidate_log_entity_path(self, entity_path: list[Log.Entity]):
        parent_entity = None
        for entity in entity_path:
            await self._consolidate_log_entity(entity, parent_entity)
            parent_entity = entity

    async def _has_entity_children(self, entity_ref: str) -> bool:
        print(
            "_has_entity_children query: %s"
            % json.dumps(
                {"bool": {"filter": {"term": {"parent_entity_ref": entity_ref}}}}
            )
        )
        resp = await self.es.search(
            index=f"{self.index}_entities",
            query={"bool": {"filter": {"term": {"parent_entity_ref": entity_ref}}}},
            size=1,
        )
        print("_has_entity_children response: %s" % json.dumps(dict(resp)))
        return bool(resp["hits"]["hits"])

    async def _get_log_entities(
        self, *, query: dict, pagination_cursor: str | None = None, limit: int = 10
    ) -> tuple[list[Entity], str | None]:
        print("_get_log_entities query: %s" % json.dumps(query))
        cursor_obj = _OffsetPaginationCursor.load(pagination_cursor)
        resp = await self.es.search(
            index=f"{self.index}_entities",
            query=query,
            sort=[{"name.keyword": "asc"}],
            from_=cursor_obj.offset,
            size=limit + 1,
        )
        print("_get_log_entities response: %s" % json.dumps(dict(resp)))

        entities = [
            Entity.model_validate(
                {
                    **hit["_source"],
                    "_id": hit["_id"],
                    "has_children": await self._has_entity_children(
                        hit["_source"]["ref"]
                    ),
                }
            )
            for hit in resp["hits"]["hits"]
        ]

        if len(entities) == limit + 1:
            next_cursor = _OffsetPaginationCursor(cursor_obj.offset + limit).serialize()
            entities.pop(-1)
        else:
            next_cursor = None

        return entities, next_cursor

    async def _get_entity_hierarchy(self, entity_ref: str) -> set[str]:
        entity = await self._get_log_entity(entity_ref)
        hierarchy = {entity.ref}
        while entity.parent_entity_ref:
            entity = await self._get_log_entity(entity.parent_entity_ref)
            hierarchy.add(entity.ref)
        return hierarchy

    async def _get_entities_hierarchy(self, entity_refs: set[str]) -> set[str]:
        parent_entities: dict[str, str] = {}
        for entity_ref in entity_refs:
            entity = await self._get_log_entity(entity_ref)
            while True:
                if entity.ref in parent_entities:
                    break
                parent_entities[entity.ref] = entity.parent_entity_ref
                if not entity.parent_entity_ref:
                    break
                entity = await self._get_log_entity(entity.parent_entity_ref)

        return entity_refs | parent_entities.keys()

    async def get_log_entities(
        self,
        authorized_entities: set[str],
        *,
        parent_entity_ref=NotImplemented,
        limit: int = 10,
        pagination_cursor: str = None,
    ) -> tuple[list[Log.Entity], str | None]:
        # please note that we use NotImplemented instead of None because None is a valid value for parent_entity_ref
        # (it means filtering on top entities)
        filter = []
        must_not = {}
        if parent_entity_ref is not NotImplemented:
            if parent_entity_ref is None:
                must_not = {"exists": {"field": "parent_entity_ref"}}
            else:
                filter.append({"term": {"parent_entity_ref": parent_entity_ref}})

        if authorized_entities:
            # get the complete hierarchy of the entity from the entity itself to the top entity
            parent_entity_ref_hierarchy = (
                await self._get_entity_hierarchy(parent_entity_ref)
                if parent_entity_ref
                else set()
            )
            # we check if we have permission on parent_entity_ref or any of its parent entities
            # if not, we have to manually filter the entities we'll have a direct or indirect visibility
            if not parent_entity_ref_hierarchy or not (
                authorized_entities & parent_entity_ref_hierarchy
            ):
                visible_entities = await self._get_entities_hierarchy(
                    authorized_entities
                )
                filter.append({"terms": {"ref": list(visible_entities)}})

        query = {"bool": {}}
        if filter:
            query["bool"]["filter"] = filter
        if must_not:
            query["bool"]["must_not"] = must_not

        return await self._get_log_entities(
            query=query, pagination_cursor=pagination_cursor, limit=limit
        )

    async def _get_log_entity(self, entity_ref: str) -> Log.Entity:
        entities, _ = await self._get_log_entities(
            query={"bool": {"filter": {"term": {"ref": entity_ref}}}}
        )
        try:
            return entities[0]
        except IndexError:
            raise UnknownModelException(entity_ref)

    async def get_log_entity(
        self, entity_ref: str, authorized_entities: set[str]
    ) -> Log.Entity:
        if authorized_entities:
            entity_ref_hierarchy = await self._get_entity_hierarchy(entity_ref)
            authorized_entities_hierarchy = await self._get_entities_hierarchy(
                authorized_entities
            )
            if not (
                entity_ref_hierarchy & authorized_entities
                or entity_ref in authorized_entities_hierarchy
            ):
                raise UnknownModelException()
        return await self._get_log_entity(entity_ref)

    async def create_log_db(self):
        await create_indices(self.es, self.index)


async def create_indices(elastic_client: AsyncElasticsearch, index_name: str):
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
                "source": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "keyword"},
                        "value": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "actor": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "extra": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {
                                    "type": "text",
                                    "fields": {"keyword": {"type": "keyword"}},
                                },
                            },
                        },
                    }
                },
                "resource": {
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                        "extra": {
                            "type": "nested",
                            "properties": {
                                "name": {"type": "keyword"},
                                "value": {
                                    "type": "text",
                                    "fields": {"keyword": {"type": "keyword"}},
                                },
                            },
                        },
                    }
                },
                "details": {
                    "type": "nested",
                    "properties": {
                        "name": {"type": "keyword"},
                        "value": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "tags": {
                    "type": "nested",
                    "properties": {
                        "ref": {"type": "keyword"},
                        "type": {"type": "keyword"},
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
                    },
                },
                "attachments": {
                    "type": "nested",
                    "properties": {
                        "name": {
                            "type": "text",
                            "fields": {"keyword": {"type": "keyword"}},
                        },
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
                            "type": "text",
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
            }
        },
    )
    await elastic_client.indices.create(
        index=f"{index_name}_entities",
        mappings={
            "properties": {
                "ref": {"type": "keyword"},
                "name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "parent_entity_ref": {"type": "keyword"},
            }
        },
        settings={
            "index": {
                "sort.field": "name.keyword",
                "sort.order": "asc",
            }
        },
    )
