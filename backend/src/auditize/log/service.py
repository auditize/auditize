import re
import string
import unicodedata
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import partial, partialmethod
from typing import Any, AsyncIterator, Awaitable, Callable, Iterator, Self
from uuid import UUID

import elasticsearch
from aiocache import Cache
from elasticsearch import AsyncElasticsearch
from elasticsearch import NotFoundError as ElasticNotFoundError
from sqlalchemy import and_, delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from auditize.api.models.cursor_pagination import (
    load_pagination_cursor,
    serialize_pagination_cursor,
)
from auditize.api.validation import (
    validate_bool,
    validate_datetime,
    validate_float,
    validate_int,
)
from auditize.config import get_config
from auditize.database import DatabaseManager
from auditize.database.sql.service import get_sql_model
from auditize.exceptions import (
    ConstraintViolation,
    InvalidPaginationCursor,
    NotFoundError,
    PermissionDenied,
    ValidationError,
)
from auditize.helpers.datetime import now
from auditize.log.index import get_read_alias, get_write_alias
from auditize.log.models import (
    CustomFieldType,
    Emitter,
    Log,
    LogCreate,
    LogImport,
    LogSearchParams,
)
from auditize.log.sql_models import LogEntity
from auditize.log_i18n_profile.models import LogLabels
from auditize.repo.service import get_repo, get_retention_period_enabled_repos
from auditize.repo.sql_models import Repo, RepoStatus

_CONSOLIDATED_LOG_ENTITIES = Cache(Cache.MEMORY)

# Builtin dimensions available for log aggregation and their matching ES field
# (all of them are root-level keyword fields with at most one value per log)
_AGGREGATION_BUILTIN_FIELDS = {
    "action_type": "action.type",
    "action_category": "action.category",
    "actor_type": "actor.type",
    "actor": "actor.ref",
    "resource_type": "resource.type",
    "resource": "resource.ref",
}

AGGREGATION_BUILTIN_DIMENSIONS = list(_AGGREGATION_BUILTIN_FIELDS)

# Custom field dimensions are expressed as "<prefix>.<field_name>",
# map each prefix to the ES path of the custom fields
_AGGREGATION_CUSTOM_FIELD_PATHS = {
    "source": "source",
    "details": "details",
    "actor": "actor.extra",
    "resource": "resource.extra",
}

AGGREGATION_CUSTOM_FIELD_PREFIXES = list(_AGGREGATION_CUSTOM_FIELD_PATHS)

# Custom field types that can be used as aggregation dimensions
# (string and JSON fields are full-text fields, datetime fields are not relevant to group by)
_AGGREGATABLE_CUSTOM_FIELD_TYPES = (
    CustomFieldType.ENUM,
    CustomFieldType.BOOLEAN,
    CustomFieldType.INTEGER,
    CustomFieldType.FLOAT,
)

# Dimensions whose value is returned as a {ref, name} object
_AGGREGATION_REF_NAME_DIMENSIONS = ("actor", "resource")


@dataclass
class LogAggregation:
    total_count: int
    # each row is a list of dimension values (in the same order as group_by) and a count
    rows: list[tuple[list[Any], int]]
    other_count: int


@dataclass
class _AggregationDimension:
    # dimension as given in group_by (e.g. "actor", "details.status"), also used as
    # the row key in the aggregation results
    name: str
    # ES field to aggregate on (e.g. "actor.ref", "details.status:enum")
    es_field: str
    # type of the custom field, None for builtin dimensions
    custom_field_type: CustomFieldType | None = None


@dataclass
class _AggregationGroup:
    keys: list[Any]
    count: int
    latest_log: dict | None


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
    def __init__(self, repo: Repo, es: AsyncElasticsearch, session: AsyncSession):
        self.repo = repo
        self.es = es
        self.session = session
        self.read_alias = get_read_alias(repo)
        self.write_alias = get_write_alias(repo)
        self._refresh = get_config().test_mode

    @classmethod
    async def _for_statuses(
        cls,
        session: AsyncSession,
        repo: Repo | UUID | str,
        statuses: list[RepoStatus] = None,
    ) -> Self:
        from auditize.repo.service import get_repo  # avoid circular import

        if isinstance(repo, str):
            repo = UUID(repo)

        if isinstance(repo, UUID):
            repo = await get_repo(session, repo)

        if statuses:
            if repo.status not in statuses:
                # NB: we could also raise a ConstraintViolation, to be discussed
                raise PermissionDenied(
                    "The repository status does not allow the requested operation"
                )

        return cls(repo, DatabaseManager.get().elastic_client, session)

    @classmethod
    async def for_reading(cls, session: AsyncSession, repo: Repo | UUID | str):
        return await cls._for_statuses(
            session, repo, [RepoStatus.ENABLED, RepoStatus.READONLY]
        )

    @classmethod
    async def for_writing(cls, session: AsyncSession, repo: Repo | UUID | str):
        return await cls._for_statuses(session, repo, [RepoStatus.ENABLED])

    @classmethod
    async def for_config(cls, session: AsyncSession, repo: Repo | UUID | str):
        return await cls._for_statuses(session, repo)

    for_maintenance = for_config

    async def check_log(self, log: LogCreate | LogImport):
        parent_entity_ref = None
        for entity in log.entity_path:
            existing_entity = await self.session.scalar(
                select(LogEntity).where(
                    LogEntity.repo_id == self.repo.id,
                    LogEntity.parent_entity_ref == parent_entity_ref,
                    LogEntity.name == entity.name,
                    LogEntity.ref != entity.ref,
                )
            )
            if existing_entity:
                raise ConstraintViolation(
                    f"Entity {entity.ref!r} is invalid, there are other logs with "
                    f"the same entity name but with another ref at the same level (same parent)"
                )
            parent_entity_ref = entity.ref

    @staticmethod
    def _is_total_es_fields_limit_exceeded(exc: elasticsearch.BadRequestError) -> bool:
        # Elasticsearch reports this error as a "document_parsing_exception"
        # with no dedicated error type, so we must rely on the error message
        try:
            reason = exc.body["error"]["caused_by"]["reason"]
        except (KeyError, TypeError):
            return False
        return reason.startswith("Limit of total fields")

    async def _save_log(self, log: Log) -> Log:
        try:
            await self.es.create(
                index=self.write_alias,
                id=str(log.id),
                document=log.model_dump(context="es"),
                refresh=self._refresh,
            )
        except elasticsearch.ConflictError:
            # NB: this should only happen in case of log import where the id
            # is provided and already exists
            raise ConstraintViolation(f"Log {log.id} already exists")
        except elasticsearch.BadRequestError as exc:
            if self._is_total_es_fields_limit_exceeded(exc):
                raise ValidationError(
                    "The log cannot be saved because the Elasticsearch limit of "
                    "total fields for this repository's index has been reached"
                )
            raise
        await self._consolidate_log_entity_path(log.entity_path)
        return log

    async def create_log(
        self,
        log_create: LogCreate,
        emitter: Emitter,
        *,
        saved_at: datetime | None = None,
    ) -> Log:
        await self.check_log(log_create)

        log_json = log_create.model_dump()
        log_json["id"] = uuid.uuid4()
        log_json["emitter"] = emitter.model_dump()
        if saved_at:
            log_json["saved_at"] = saved_at

        return await self._save_log(Log.model_validate(log_json))

    async def import_log(self, log_import: LogImport, emitter: Emitter) -> Log:
        await self.check_log(log_import)

        log_json = log_import.model_dump(exclude_unset=True)
        log_json.setdefault("id", uuid.uuid4())
        log_json["emitter"] = emitter.model_dump()
        return await self._save_log(Log.model_validate(log_json))

    async def save_log_attachment(self, log_id: UUID, attachment: Log.Attachment):
        try:
            await self.es.update(
                index=self.write_alias,
                id=str(log_id),
                script={
                    "source": "ctx._source.attachments.add(params.attachment)",
                    "params": {"attachment": attachment.model_dump()},
                },
                refresh=self._refresh,
            )
        except ElasticNotFoundError:
            raise NotFoundError()

    @staticmethod
    def _build_authorized_entities_es_query(
        authorized_entities: set[str] | None,
    ) -> dict | None:
        if not authorized_entities:
            return None
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
    def _check_log_visibility(log: Log, authorized_entities: set[str]):
        if (
            authorized_entities
            and not set(entity.ref for entity in log.entity_path) & authorized_entities
        ):
            raise NotFoundError()

    async def get_log(self, log_id: UUID, authorized_entities: set[str]) -> Log:
        try:
            resp = await self.es.get(
                index=self.read_alias,
                id=str(log_id),
                source_excludes=["attachments.data"],
            )
        except ElasticNotFoundError:
            raise NotFoundError()

        log = Log.model_validate(resp["_source"], context="es")
        self._check_log_visibility(log, authorized_entities)

        return log

    async def get_log_attachment(
        self, log_id: UUID, attachment_idx: int, authorized_entities: set[str]
    ) -> Log.Attachment:
        # NB: we retrieve all attachments here, which is not really efficient if the log contains
        # more than 1 log, unfortunately ES does not a let us retrieve a nested object to a specific
        # array index unless adding an extra metadata such as "index" to the stored document
        try:
            resp = await self.es.get(index=self.read_alias, id=str(log_id))
        except ElasticNotFoundError:
            raise NotFoundError()

        self._check_log_visibility(
            Log.model_validate(resp["_source"], context="es"),
            authorized_entities,
        )

        try:
            attachment = resp["_source"]["attachments"][attachment_idx]
        except IndexError:
            raise NotFoundError()

        return Log.Attachment.model_validate(attachment)

    @staticmethod
    def _nested_filter(path, filter):
        return {
            "nested": {
                "path": path,
                "query": {"bool": {"filter": [filter]}},
            }
        }

    @classmethod
    def _nested_filter_term(cls, path, name, value):
        return cls._nested_filter(path, {"term": {name: value}})

    @classmethod
    def _query_filter(cls, query: str):
        """
        Build a filter to match words in the query against the searchable fields
        (string and JSON custom fields gathered in custom_fields_text, resource.name).
        Each word must match indifferently of the field they are in the log.
        """
        return {
            "bool": {
                "must": [
                    {
                        "bool": {
                            "should": [
                                {"match": {"custom_fields_text": word}},
                                {"match": {"resource.name": word}},
                            ],
                            "minimum_should_match": 1,
                        }
                    }
                    for word in cls._split_words(query)
                ]
            }
        }

    @staticmethod
    def _get_custom_field_type_from_source(
        source: dict, path: str, field_name: str
    ) -> CustomFieldType:
        """
        Example:
        - source: {"actor": {"extra": {"role:enum": "admin", "age:integer": 42}}}
        - path: "actor.extra"
        - field_name: "age"
        - returns: CustomFieldType.INTEGER
        """
        custom_fields = source
        for key in path.split("."):
            custom_fields = custom_fields[key]
        for key in custom_fields:
            name, field_type = key.rsplit(":", 1)
            if name == field_name:
                return CustomFieldType(field_type)
        # NB: fallback to string type, this should never happen
        return CustomFieldType.STRING

    async def _find_custom_field_type(
        self, path: str, field_name: str
    ) -> CustomFieldType | None:
        """Return the custom field type from the most recent log having it, or None if no log has it."""
        resp = await self.es.search(
            index=self.read_alias,
            query={"term": {f"{path}_fields": field_name}},
            sort=[{"emitted_at": {"order": "desc"}}],
            source_includes=[f"{path}.{field_name}:*"],
            size=1,
        )

        hits = resp["hits"]["hits"]
        if hits:
            return self._get_custom_field_type_from_source(
                hits[0]["_source"], path, field_name
            )
        return None

    async def _get_custom_field_type(
        self, path: str, field_name: str
    ) -> CustomFieldType:
        field_type = await self._find_custom_field_type(path, field_name)
        # NB: fallback to string type, this should never happen
        return field_type or CustomFieldType.STRING

    async def _custom_field_search_filter(
        self, path: str, field_name: str, field_value: str
    ) -> dict:
        field_type = await self._get_custom_field_type(path, field_name)
        field = f"{path}.{field_name}:{field_type}"
        match field_type:
            case CustomFieldType.ENUM:
                return {"term": {field: field_value}}
            case CustomFieldType.BOOLEAN:
                return {"term": {field: validate_bool(field_value)}}
            case CustomFieldType.INTEGER:
                return {"term": {field: validate_int(field_value)}}
            case CustomFieldType.FLOAT:
                return {"term": {field: validate_float(field_value)}}
            case CustomFieldType.DATETIME:
                # NB: search on the precise value does not really make sense for a datetime field,
                # range search will be implemented in a future version.
                return {"term": {field: validate_datetime(field_value)}}
            case _:
                return {"match": {field: {"query": field_value, "operator": "and"}}}

    async def _custom_fields_search_filter(
        self, path: str, fields: dict[str, str]
    ) -> list[dict]:
        return [
            await self._custom_field_search_filter(path, name, value)
            for name, value in fields.items()
        ]

    async def _build_es_query(
        self,
        search_params: LogSearchParams | None = None,
        *,
        authorized_entities: set[str] | None = None,
    ) -> dict | None:
        sp = search_params
        filter = []

        if sp:
            if sp.query:
                filter.append(self._query_filter(sp.query))
            if sp.action_type:
                filter.append({"term": {"action.type": sp.action_type}})
            if sp.action_category:
                filter.append({"term": {"action.category": sp.action_category}})
            if sp.source:
                filter.extend(
                    await self._custom_fields_search_filter("source", sp.source)
                )
            if sp.actor_type:
                filter.append({"term": {"actor.type": sp.actor_type}})
            if sp.actor_name:
                filter.append({"term": {"actor.name.keyword": sp.actor_name}})
            if sp.actor_ref:
                filter.append({"term": {"actor.ref": sp.actor_ref}})
            if sp.actor_extra:
                filter.extend(
                    await self._custom_fields_search_filter(
                        "actor.extra", sp.actor_extra
                    )
                )
            if sp.resource_type:
                filter.append({"term": {"resource.type": sp.resource_type}})
            if sp.resource_name:
                filter.append({"term": {"resource.name.keyword": sp.resource_name}})
            if sp.resource_ref:
                filter.append({"term": {"resource.ref": sp.resource_ref}})
            if sp.resource_extra:
                filter.extend(
                    await self._custom_fields_search_filter(
                        "resource.extra", sp.resource_extra
                    )
                )
            if sp.details:
                filter.extend(
                    await self._custom_fields_search_filter("details", sp.details)
                )
            if sp.tag_ref:
                filter.append(self._nested_filter_term("tags", "tags.ref", sp.tag_ref))
            if sp.tag_type:
                filter.append(
                    self._nested_filter_term("tags", "tags.type", sp.tag_type)
                )
            if sp.tag_name:
                filter.append(
                    self._nested_filter_term("tags", "tags.name.keyword", sp.tag_name)
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
                    self._nested_filter(
                        "attachments",
                        {
                            "match": {
                                "attachments.name": {
                                    "query": sp.attachment_name,
                                    "operator": "and",
                                }
                            }
                        },
                    )
                )

            if sp.attachment_type:
                filter.append(
                    self._nested_filter_term(
                        "attachments", "attachments.type", sp.attachment_type
                    )
                )
            if sp.attachment_mime_type:
                filter.append(
                    self._nested_filter_term(
                        "attachments", "attachments.mime_type", sp.attachment_mime_type
                    )
                )
            if sp.entity_ref:
                filter.append(
                    self._nested_filter_term(
                        "entity_path", "entity_path.ref", sp.entity_ref
                    )
                )
            if sp.since:
                filter.append({"range": {"emitted_at": {"gte": sp.since}}})
            if sp.until:
                # don't want to miss logs saved at the same second, meaning that the "until: ...23:59:59" criterion
                # will also include logs saved at 23:59:59.500 for instance
                filter.append(
                    {
                        "range": {
                            "emitted_at": {"lte": sp.until.replace(microsecond=999999)}
                        }
                    }
                )

        if authorized_entities:
            filter.append(self._build_authorized_entities_es_query(authorized_entities))

        return {"bool": {"filter": filter}} if filter else None

    async def get_logs(
        self,
        *,
        authorized_entities: set[str] = None,
        search_params: LogSearchParams = None,
        include_attachment_data: bool = False,
        sort_by_saved_at: bool = False,
        limit: int = 10,
        pagination_cursor: str = None,
    ) -> tuple[list[Log], str | None]:
        resp = await self.es.search(
            index=self.read_alias,
            query=await self._build_es_query(
                search_params, authorized_entities=authorized_entities
            ),
            search_after=(
                load_pagination_cursor(pagination_cursor) if pagination_cursor else None
            ),
            source_excludes=None if include_attachment_data else ["attachments.data"],
            sort=[
                {
                    "saved_at" if sort_by_saved_at else "emitted_at": "desc",
                    "log_id": "desc",
                }
            ],
            size=limit + 1,
            track_total_hits=False,
        )
        hits = list(resp["hits"]["hits"])

        # we previously fetched one extra log to check if there are more logs to fetch
        if len(hits) == limit + 1:
            # there is still more logs to fetch, so we need to return a next_cursor based on the last log WITHIN the
            # limit range
            next_cursor = serialize_pagination_cursor(hits[-2]["sort"])
            hits.pop(-1)
        else:
            next_cursor = None

        logs = [Log.model_validate(hit["_source"], context="es") for hit in hits]

        return logs, next_cursor

    async def get_newest_log(
        self,
        search_params: LogSearchParams | None = None,
        *,
        authorized_entities: set[str] = None,
    ) -> Log | None:
        resp = await self.es.search(
            index=self.read_alias,
            query=await self._build_es_query(
                search_params, authorized_entities=authorized_entities
            ),
            sort=[{"emitted_at": "desc", "log_id": "desc"}],
            size=1,
        )
        hits = resp["hits"]["hits"]
        if not hits:
            return None
        return Log.model_validate(hits[0]["_source"], context="es")

    async def get_log_count(self) -> int:
        resp = await self.es.count(
            index=self.read_alias,
            query={"match_all": {}},
        )
        return resp["count"]

    async def count_logs(
        self,
        *,
        authorized_entities: set[str] = None,
        search_params: LogSearchParams = None,
    ) -> int:
        resp = await self.es.count(
            index=self.read_alias,
            query=await self._build_es_query(
                search_params, authorized_entities=authorized_entities
            ),
        )
        return resp["count"]

    async def _resolve_aggregation_dimension(
        self, dimension: str
    ) -> _AggregationDimension:
        """
        Examples:
        - "actor" => _AggregationDimension("actor", "actor.ref", None)
        - "details.status" (enum) => _AggregationDimension(
            "details.status", "details.status:enum", CustomFieldType.ENUM
          )
        - "actor.age" (integer) => _AggregationDimension(
            "actor.age", "actor.extra.age:integer", CustomFieldType.INTEGER
          )
        - "foo.bar", "details.unknown", "details.comment" (string) => ValidationError
        """
        if dimension in _AGGREGATION_BUILTIN_FIELDS:
            return _AggregationDimension(
                dimension, _AGGREGATION_BUILTIN_FIELDS[dimension]
            )

        prefix, _, field_name = dimension.partition(".")
        path = _AGGREGATION_CUSTOM_FIELD_PATHS.get(prefix)
        if not path or not field_name:
            raise ValidationError(
                f"Invalid dimension {dimension!r}, expected one of "
                f"{', '.join(AGGREGATION_BUILTIN_DIMENSIONS)} or a custom field "
                f"as <prefix>.<field_name> with prefix one of "
                f"{', '.join(AGGREGATION_CUSTOM_FIELD_PREFIXES)}"
            )

        field_type = await self._find_custom_field_type(path, field_name)
        if not field_type:
            raise ValidationError(f"Unknown custom field {dimension!r}")
        if field_type not in _AGGREGATABLE_CUSTOM_FIELD_TYPES:
            raise ValidationError(
                f"Custom field {dimension!r} of type {field_type} cannot be used as "
                f"dimension, expected one of these types: "
                f"{', '.join(_AGGREGATABLE_CUSTOM_FIELD_TYPES)}"
            )
        return _AggregationDimension(
            dimension, f"{path}.{field_name}:{field_type}", field_type
        )

    async def _resolve_aggregation_dimensions(
        self, group_by: list[str]
    ) -> list[_AggregationDimension]:
        if not 1 <= len(group_by) <= 2:
            raise ValidationError("group_by must contain 1 or 2 dimensions")
        if len(set(group_by)) != len(group_by):
            raise ValidationError("group_by must not contain the same dimension twice")
        return [
            await self._resolve_aggregation_dimension(dimension)
            for dimension in group_by
        ]

    @staticmethod
    def _get_aggregation_name_dimensions(
        dimensions: list[_AggregationDimension],
    ) -> list[str]:
        return [
            dim.name
            for dim in dimensions
            if dim.name in _AGGREGATION_REF_NAME_DIMENSIONS
        ]

    @classmethod
    def _build_aggregation(
        cls, dimensions: list[_AggregationDimension], limit: int
    ) -> dict:
        # NB: logs without value for a dimension are not part of any group
        terms = [{"field": dim.es_field} for dim in dimensions]
        params = {
            "size": limit,
            "order": [{"_count": "desc"}, {"_key": "asc"}],
        }
        if len(terms) == 1:
            aggregation = {"terms": {**terms[0], **params}}
        else:
            aggregation = {"multi_terms": {"terms": terms, **params}}

        # Get the names of actors / resources from the most recent log of each group
        name_dimensions = cls._get_aggregation_name_dimensions(dimensions)
        if name_dimensions:
            aggregation["aggs"] = {
                "latest": {
                    "top_hits": {
                        "size": 1,
                        "sort": [{"emitted_at": "desc"}],
                        "_source": {
                            "includes": [f"{dim}.name" for dim in name_dimensions]
                        },
                    }
                }
            }

        return aggregation

    @classmethod
    def _get_aggregation_groups(
        cls, dimensions: list[_AggregationDimension], buckets: list[dict]
    ) -> list[_AggregationGroup]:
        with_latest_log = bool(cls._get_aggregation_name_dimensions(dimensions))
        return [
            _AggregationGroup(
                # terms returns a single key, multi_terms returns a list of keys
                keys=bucket["key"] if len(dimensions) > 1 else [bucket["key"]],
                count=bucket["doc_count"],
                latest_log=(
                    bucket["latest"]["hits"]["hits"][0]["_source"]
                    if with_latest_log
                    else None
                ),
            )
            for bucket in buckets
        ]

    @staticmethod
    def _get_aggregation_value(
        dimension: _AggregationDimension, key: Any, latest_log: dict | None
    ) -> Any:
        if dimension.name in _AGGREGATION_REF_NAME_DIMENSIONS:
            return {"ref": key, "name": latest_log[dimension.name]["name"]}
        # ES returns boolean keys as 1 / 0
        if dimension.custom_field_type == CustomFieldType.BOOLEAN:
            return bool(key)
        return key

    async def aggregate_logs(
        self,
        *,
        group_by: list[str],
        authorized_entities: set[str] = None,
        search_params: LogSearchParams = None,
        limit: int,
    ) -> LogAggregation:
        dimensions = await self._resolve_aggregation_dimensions(group_by)

        resp = await self.es.search(
            index=self.read_alias,
            query=await self._build_es_query(
                search_params, authorized_entities=authorized_entities
            ),
            size=0,
            track_total_hits=True,
            aggregations={"groups": self._build_aggregation(dimensions, limit)},
        )
        total_count = resp["hits"]["total"]["value"]
        groups = self._get_aggregation_groups(
            dimensions, resp["aggregations"]["groups"]["buckets"]
        )

        rows = [
            (
                [
                    self._get_aggregation_value(dimension, key, group.latest_log)
                    for dimension, key in zip(dimensions, group.keys)
                ],
                group.count,
            )
            for group in groups
        ]
        return LogAggregation(
            total_count=total_count,
            rows=rows,
            other_count=total_count - sum(count for _, count in rows),
        )

    async def get_storage_size(self) -> int:
        resp = await self.es.indices.stats(index=self.read_alias)
        return resp["_all"]["primaries"]["store"]["size_in_bytes"]

    async def _get_paginated_agg_multi_fields(
        self,
        *,
        nested: str = None,
        nested_filter: dict = None,
        fields: list[str],
        query: dict = None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[list[str]], str]:
        after = load_pagination_cursor(pagination_cursor) if pagination_cursor else None

        aggregations = {
            "group_by": {
                "composite": {
                    "size": limit,
                    "sources": [
                        {field: {"terms": {"field": field, "order": "asc"}}}
                        for field in fields
                    ],
                    **({"after": after} if after else {}),
                }
            },
        }
        if nested_filter:
            # restrict the aggregation itself to the nested sub-documents matching
            # nested_filter, as opposed to `query` which only filters top-level documents
            # (a document with at least one matching nested sub-document still has all its
            # nested sub-documents, matching or not, included in the aggregation)
            aggregations = {
                "matching": {
                    "filter": nested_filter,
                    "aggs": aggregations,
                }
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

        resp = await self.es.search(
            index=self.read_alias,
            query=query,
            aggregations=aggregations,
            size=0,
        )

        if nested:
            group_by_result = resp["aggregations"]["nested_group_by"]
        else:
            group_by_result = resp["aggregations"]
        if nested_filter:
            group_by_result = group_by_result["matching"]
        group_by_result = group_by_result["group_by"]

        if len(group_by_result["buckets"]) == limit and "after_key" in group_by_result:
            next_cursor = serialize_pagination_cursor(group_by_result["after_key"])
        else:
            next_cursor = None

        values = [
            [bucket["key"][field] for field in fields]
            for bucket in group_by_result["buckets"]
        ]

        return values, next_cursor

    async def _get_paginated_agg_single_field(
        self,
        *,
        nested: str = None,
        field: str,
        authorized_entities: set[str] | None = None,
        search_params: LogSearchParams | None = None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[str], str]:
        values, next_cursor = await self._get_paginated_agg_multi_fields(
            nested=nested,
            fields=[field],
            query=await self._build_es_query(
                search_params, authorized_entities=authorized_entities
            ),
            limit=limit,
            pagination_cursor=pagination_cursor,
        )
        return [value[0] for value in values], next_cursor

    get_log_action_categories = partialmethod(
        _get_paginated_agg_single_field, field="action.category"
    )

    async def get_log_action_types(
        self,
        *,
        authorized_entities: set[str] | None = None,
        action_category: str | None = None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[str], str]:
        return await self._get_paginated_agg_single_field(
            field="action.type",
            authorized_entities=authorized_entities,
            search_params=(
                LogSearchParams(action_category=action_category)
                if action_category
                else None
            ),
            limit=limit,
            pagination_cursor=pagination_cursor,
        )

    get_log_tag_types = partialmethod(
        _get_paginated_agg_single_field, nested="tags", field="tags.type"
    )

    get_log_actor_types = partialmethod(
        _get_paginated_agg_single_field, field="actor.type"
    )

    get_log_resource_types = partialmethod(
        _get_paginated_agg_single_field, field="resource.type"
    )

    get_log_attachment_types = partialmethod(
        _get_paginated_agg_single_field, nested="attachments", field="attachments.type"
    )

    get_log_attachment_mime_types = partialmethod(
        _get_paginated_agg_single_field,
        nested="attachments",
        field="attachments.mime_type",
    )

    @staticmethod
    def _split_words(value: str) -> list[str]:
        """
        Elasticsearch "prefix" query does not use the search_analyzer, so we have
        to implement the equivalent processing in Python.
        """

        # De-accentuate the value
        normalized = unicodedata.normalize("NFD", value)
        unaccented = normalized.encode("ascii", "ignore").decode("utf8")

        # Lowercase
        lowercased = unaccented.lower()

        # Split by spaces / non-alphanumeric characters, which means
        # that only actual words are kept
        words = re.split("[" + string.whitespace + string.punctuation + "]", lowercased)

        # Filter out empty words
        return list(filter(bool, words))

    async def _get_aggregated_name_ref_pairs(
        self,
        *,
        path: str,
        nested: bool = False,
        authorized_entities: set[str] | None = None,
        search: str | None = None,
        limit: int = 10,
        pagination_cursor: str | None = None,
    ) -> tuple[list[tuple[str, str]], str]:
        filter = []
        if search:
            words_query = {
                "bool": {
                    "filter": [
                        {"prefix": {f"{path}.name": word}}
                        for word in self._split_words(search)
                    ]
                }
            }
            if nested:
                words_query = {"nested": {"path": path, "query": words_query}}
            filter.append(words_query)
        if authorized_entities:
            filter.append(self._build_authorized_entities_es_query(authorized_entities))

        values, next_cursor = await self._get_paginated_agg_multi_fields(
            nested=path if nested else None,
            query={"bool": {"filter": filter}} if filter else None,
            fields=[f"{path}.name.keyword", f"{path}.ref"],
            limit=limit,
            pagination_cursor=pagination_cursor,
        )
        return [tuple(value) for value in values], next_cursor

    get_log_actor_names = partialmethod(_get_aggregated_name_ref_pairs, path="actor")

    get_log_resource_names = partialmethod(
        _get_aggregated_name_ref_pairs, path="resource"
    )

    get_log_tag_names = partialmethod(
        _get_aggregated_name_ref_pairs, path="tags", nested=True
    )

    async def get_log_simple_tag_types(
        self,
        *,
        authorized_entities: set[str] | None = None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[str], str]:
        values, next_cursor = await self._get_paginated_agg_multi_fields(
            nested="tags",
            nested_filter={"bool": {"must_not": {"exists": {"field": "tags.ref"}}}},
            fields=["tags.type"],
            query=await self._build_es_query(
                None, authorized_entities=authorized_entities
            ),
            limit=limit,
            pagination_cursor=pagination_cursor,
        )
        return [value[0] for value in values], next_cursor

    async def get_log_actor(
        self, actor_ref: str, authorized_entities: set[str]
    ) -> Log.Actor:
        log = await self.get_newest_log(
            LogSearchParams(actor_ref=actor_ref),
            authorized_entities=authorized_entities,
        )
        if not log or not log.actor:
            raise NotFoundError(f"Actor {actor_ref!r} not found")
        return log.actor

    async def get_log_resource(
        self, resource_ref: str, authorized_entities: set[str]
    ) -> Log.Resource:
        log = await self.get_newest_log(
            LogSearchParams(resource_ref=resource_ref),
            authorized_entities=authorized_entities,
        )
        if not log or not log.resource:
            raise NotFoundError(f"Resource {resource_ref!r} not found")
        return log.resource

    async def get_log_tag(self, tag_ref: str, authorized_entities: set[str]) -> Log.Tag:
        log = await self.get_newest_log(
            LogSearchParams(tag_ref=tag_ref),
            authorized_entities=authorized_entities,
        )
        if log:
            for tag in log.tags:
                if tag.ref == tag_ref:
                    return tag
        raise NotFoundError(f"Tag {tag_ref!r} not found")

    async def _get_custom_fields(
        self,
        *,
        path: str,
        authorized_entities: set[str] | None = None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[tuple[str, CustomFieldType]], str | None]:
        after = load_pagination_cursor(pagination_cursor) if pagination_cursor else None

        aggregations = {
            "by_name": {
                "composite": {
                    "size": limit,
                    "sources": [
                        {
                            "name": {
                                "terms": {
                                    "field": f"{path}_fields",
                                    "order": "asc",
                                }
                            }
                        }
                    ],
                    **({"after": after} if after else {}),
                },
                "aggs": {
                    "latest": {
                        "top_hits": {
                            "size": 1,
                            "sort": [{"emitted_at": {"order": "desc"}}],
                            "_source": {"includes": [path]},
                        }
                    }
                },
            }
        }

        resp = await self.es.search(
            index=self.read_alias,
            query=self._build_authorized_entities_es_query(authorized_entities),
            aggregations=aggregations,
            size=0,
        )

        group_by_result = resp["aggregations"]["by_name"]

        results = []
        for bucket in group_by_result["buckets"]:
            custom_field_name = bucket["key"]["name"]
            latest_log = bucket["latest"]["hits"]["hits"][0]["_source"]
            custom_field_type = self._get_custom_field_type_from_source(
                latest_log, path, custom_field_name
            )
            results.append((custom_field_name, custom_field_type))

        if len(group_by_result["buckets"]) == limit and "after_key" in group_by_result:
            next_cursor = serialize_pagination_cursor(group_by_result["after_key"])
        else:
            next_cursor = None

        return results, next_cursor

    get_log_details_fields = partialmethod(_get_custom_fields, path="details")

    get_log_source_fields = partialmethod(_get_custom_fields, path="source")

    get_log_actor_extra_fields = partialmethod(_get_custom_fields, path="actor.extra")

    get_log_resource_extra_fields = partialmethod(
        _get_custom_fields, path="resource.extra"
    )

    async def _get_custom_field_enum_values(
        self,
        *,
        path: str,
        field_name: str,
        authorized_entities: set[str] | None = None,
        limit: int,
        pagination_cursor: str | None,
    ) -> tuple[list[str], str | None]:
        after = load_pagination_cursor(pagination_cursor) if pagination_cursor else None

        aggregations = {
            "distinct_values": {
                "composite": {
                    "size": limit,
                    "sources": [
                        {
                            "value_enum": {
                                "terms": {
                                    "field": f"{path}.{field_name}:{CustomFieldType.ENUM}",
                                    "order": "asc",
                                }
                            }
                        }
                    ],
                    **({"after": after} if after else {}),
                }
            }
        }

        resp = await self.es.search(
            index=self.read_alias,
            query=self._build_authorized_entities_es_query(authorized_entities),
            aggregations=aggregations,
            size=0,
        )

        group_by_result = resp["aggregations"]["distinct_values"]

        if len(group_by_result["buckets"]) == limit and "after_key" in group_by_result:
            next_cursor = serialize_pagination_cursor(group_by_result["after_key"])
        else:
            next_cursor = None

        enum_values = [
            bucket["key"]["value_enum"] for bucket in group_by_result["buckets"]
        ]

        return enum_values, next_cursor

    get_details_enum_values = partialmethod(
        _get_custom_field_enum_values, path="details"
    )
    get_source_enum_values = partialmethod(_get_custom_field_enum_values, path="source")
    get_resource_extra_enum_values = partialmethod(
        _get_custom_field_enum_values, path="resource.extra"
    )
    get_actor_extra_enum_values = partialmethod(
        _get_custom_field_enum_values, path="actor.extra"
    )

    async def _purge_orphan_log_entity_if_needed(self, entity: LogEntity):
        """
        This function assumes that the entity has no children and delete it if it has no associated logs.
        It performs the same operation recursively on its ancestors.
        """
        associated_logs, _ = await self.get_logs(
            search_params=LogSearchParams(entity_ref=entity.ref), limit=1
        )
        if not associated_logs:
            await self.session.delete(entity)
            await self.session.flush()
            print(
                f"Deleted orphan log entity {entity!r} from log repository {self.repo.log_db_name!r}"
            )
            parent_entity = await self.session.scalar(
                select(LogEntity).where(
                    LogEntity.repo_id == self.repo.id,
                    LogEntity.id == entity.parent_entity_id,
                )
            )
            if parent_entity and not parent_entity.has_children:
                await self._purge_orphan_log_entity_if_needed(parent_entity)

    async def _purge_orphan_log_entities(self):
        result = await self.session.execute(
            select(LogEntity).where(
                LogEntity.repo_id == self.repo.id,
                LogEntity.has_children == False,
            )
        )
        leaf_entities = result.scalars().all()

        for entity in leaf_entities:
            await self._purge_orphan_log_entity_if_needed(entity)

        await self.session.commit()

    async def _apply_log_retention_period(self):
        if not self.repo.retention_period:
            return

        resp = await self.es.delete_by_query(
            index=self.write_alias,
            query={
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "emitted_at": {
                                    "lt": (
                                        now()
                                        - timedelta(days=self.repo.retention_period)
                                    )
                                }
                            }
                        }
                    ]
                }
            },
            refresh=self._refresh,
        )
        if resp["deleted"] > 0:
            print(
                f"Deleted {resp['deleted']} logs older than {self.repo.retention_period} days "
                f"in log repository {self.repo.name!r}"
            )
            await self._purge_orphan_log_entities()

    @classmethod
    async def apply_log_retention_period(
        cls, session: AsyncSession, repo: UUID | Repo = None
    ):
        if repo:
            repos = [await get_repo(session, repo)]
        else:
            repos = await get_retention_period_enabled_repos(session)

        for repo in repos:
            service = await cls.for_maintenance(session, repo)
            await service._apply_log_retention_period()
            # FIXME: we should also delete the consolidated entities that are not referenced by any log

    async def _consolidate_log_entity(
        self, entity: Log.EntityPathNode, parent_entity_id: UUID | None
    ) -> UUID:
        cache_key = "\t".join(
            (
                str(self.repo.id),
                entity.ref,
                entity.name,
                str(parent_entity_id) if parent_entity_id else "",
            )
        )
        if entity_id := await _CONSOLIDATED_LOG_ENTITIES.get(cache_key):
            return entity_id

        result = await self.session.execute(
            insert(LogEntity)
            .values(
                repo_id=self.repo.id,
                ref=entity.ref,
                name=entity.name,
                parent_entity_id=parent_entity_id,
            )
            .on_conflict_do_update(
                index_elements=[LogEntity.repo_id, LogEntity.ref],
                set_=dict(
                    name=entity.name,
                    parent_entity_id=parent_entity_id,
                ),
            )
            .returning(LogEntity.id)
        )
        entity_id = result.scalar_one()
        await self.session.commit()

        await _CONSOLIDATED_LOG_ENTITIES.set(cache_key, entity_id)
        return entity_id

    async def _consolidate_log_entity_path(self, entity_path: list[Log.EntityPathNode]):
        parent_entity_id = None
        for entity in entity_path:
            parent_entity_id = await self._consolidate_log_entity(
                entity, parent_entity_id
            )

    async def _has_entity_children(self, entity_ref: str) -> bool:
        return (
            await self.session.execute(
                select(LogEntity)
                .where(
                    LogEntity.repo_id == self.repo.id,
                    LogEntity.parent_entity_ref == entity_ref,
                )
                .limit(1)
            )
        ).scalar() is not None

    async def _get_log_entities(
        self,
        *,
        filters: list[Any],
        pagination_cursor: str | None = None,
        limit: int = 10,
    ) -> tuple[list[LogEntity], str | None]:
        filters = [LogEntity.repo_id == self.repo.id] + filters
        cursor_obj = _OffsetPaginationCursor.load(pagination_cursor)
        result = await self.session.execute(
            select(LogEntity)
            .where(*filters)
            .order_by(LogEntity.name)
            .offset(cursor_obj.offset)
            .limit(limit + 1)
        )
        entities = result.scalars().all()
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
        search: str | None = None,
        limit: int = 10,
        pagination_cursor: str = None,
    ) -> tuple[list[LogEntity], str | None]:
        # please note that we use NotImplemented instead of None because None is a valid value for parent_entity_ref
        # (it means filtering on top entities)
        filters = []
        if parent_entity_ref is not NotImplemented:
            filters.append(LogEntity.parent_entity_ref == parent_entity_ref)

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
                filters.append(LogEntity.ref.in_(visible_entities))

        if search:
            filters.append(LogEntity.name.ilike(f"%{search}%"))

        return await self._get_log_entities(
            filters=filters, pagination_cursor=pagination_cursor, limit=limit
        )

    async def _get_log_entity(self, entity_ref: str) -> LogEntity:
        return await get_sql_model(
            self.session,
            LogEntity,
            and_(LogEntity.repo_id == self.repo.id, LogEntity.ref == entity_ref),
        )

    async def get_log_entity(
        self, entity_ref: str, authorized_entities: set[str]
    ) -> Log.EntityPathNode:
        if authorized_entities:
            entity_ref_hierarchy = await self._get_entity_hierarchy(entity_ref)
            authorized_entities_hierarchy = await self._get_entities_hierarchy(
                authorized_entities
            )
            if not (
                entity_ref_hierarchy & authorized_entities
                or entity_ref in authorized_entities_hierarchy
            ):
                raise NotFoundError()
        return await self._get_log_entity(entity_ref)

    async def iter_on_log_entity_path(self, entity: LogEntity) -> Iterator[LogEntity]:
        if entity.parent_entity_id:
            parent_entity = await get_sql_model(
                self.session, LogEntity, LogEntity.id == entity.parent_entity_id
            )
            async for ent in self.iter_on_log_entity_path(parent_entity):
                yield ent
        yield entity

    async def empty_log_db(self):
        await self.es.delete_by_query(
            index=self.write_alias,
            query={"match_all": {}},
            wait_for_completion=self._refresh,
            refresh=self._refresh,
        )
        await self.session.execute(
            delete(LogEntity).where(LogEntity.repo_id == self.repo.id)
        )
        await self.session.commit()

    @staticmethod
    async def _iter_paginated_items[T](
        func: Callable[..., Awaitable[tuple[list[T], str | None]]],
    ) -> AsyncIterator[T]:
        cursor = None
        while True:
            items, next_cursor = await func(limit=100, pagination_cursor=cursor)
            for item in items:
                yield item
            if not next_cursor:
                break
            cursor = next_cursor

    @staticmethod
    async def _get_custom_field_enum_values_as_template(
        fields: dict[str, str],
        func: Callable[..., Awaitable[tuple[list[str], str | None]]],
    ) -> dict[str, dict[str, str]]:
        result = {}
        for field_name in fields:
            enum_values = {
                val: ""
                async for val in LogService._iter_paginated_items(
                    partial(func, field_name=field_name)
                )
            }
            if enum_values:
                result[field_name] = enum_values
        return result

    async def _get_field_values_as_template(
        self,
        func: Callable[..., Awaitable[tuple[list[Any], str | None]]],
        *,
        value: Callable[[Any], str] = lambda item: item,
    ) -> dict[str, str]:
        result = {}
        async for item in self._iter_paginated_items(func):
            result[value(item)] = ""
        return result

    async def get_log_translation_template(self) -> LogLabels:
        labels = LogLabels()

        ###
        # Action
        ###
        labels.action_type = await self._get_field_values_as_template(
            self.get_log_action_types
        )
        labels.action_category = await self._get_field_values_as_template(
            self.get_log_action_categories
        )

        ###
        # Source
        ###
        labels.source_field_name = await self._get_field_values_as_template(
            self.get_log_source_fields, value=lambda val: val[0]
        )
        labels.source_field_value_enum = (
            await self._get_custom_field_enum_values_as_template(
                labels.source_field_name, self.get_source_enum_values
            )
        )

        ###
        # Actor
        ###
        labels.actor_type = await self._get_field_values_as_template(
            self.get_log_actor_types
        )
        labels.actor_extra_field_name = await self._get_field_values_as_template(
            self.get_log_actor_extra_fields, value=lambda val: val[0]
        )
        labels.actor_extra_field_value_enum = (
            await self._get_custom_field_enum_values_as_template(
                labels.actor_extra_field_name, self.get_actor_extra_enum_values
            )
        )

        ###
        # Resource
        ###
        labels.resource_type = await self._get_field_values_as_template(
            self.get_log_resource_types
        )
        labels.resource_extra_field_name = await self._get_field_values_as_template(
            self.get_log_resource_extra_fields, value=lambda val: val[0]
        )
        labels.resource_extra_field_value_enum = (
            await self._get_custom_field_enum_values_as_template(
                labels.resource_extra_field_name, self.get_resource_extra_enum_values
            )
        )

        ###
        # Details
        ###
        labels.detail_field_name = await self._get_field_values_as_template(
            self.get_log_details_fields, value=lambda val: val[0]
        )
        labels.detail_field_value_enum = (
            await self._get_custom_field_enum_values_as_template(
                labels.detail_field_name, self.get_details_enum_values
            )
        )

        ###
        # Tag
        ###
        labels.tag_type = await self._get_field_values_as_template(
            self.get_log_tag_types
        )

        return labels
