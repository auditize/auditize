from datetime import datetime, timezone
from typing import NamedTuple

from auditize.exceptions import NotFoundError
from auditize.log.models import CustomFieldType, LogSearchParams
from auditize.log.service import (
    AGGREGATABLE_CUSTOM_FIELD_TYPES,
    CUSTOM_FIELD_GROUP_PATHS,
    LogService,
)
from auditize.mcp.models import (
    ActionDescription,
    ActionTypeStats,
    ActorTypeStats,
    CustomFieldGroups,
    CustomFieldStats,
    DistinctCount,
    RepoDescription,
    ResourceTypeStats,
    TruncatedDict,
    TruncatedList,
    TypeLogCount,
)

# Limits of describe_repo / describe_action results
_MAX_ACTION_TYPES = 50
_MAX_ENUM_VALUES = 20
_MAX_FIELDS_PER_GROUP = 100

# Same value as the ES default, distinct counts above it are approximate
_CARDINALITY_PRECISION_THRESHOLD = 3000


class _MappedCustomField(NamedTuple):
    # custom field known by the index mapping
    group: str
    name: str
    type: CustomFieldType

    @property
    def es_field(self) -> str:
        return f"{CUSTOM_FIELD_GROUP_PATHS[self.group]}.{self.name}:{self.type}"


class McpLogService(LogService):
    @staticmethod
    def _build_cardinality_aggregation(field: str) -> dict:
        return {
            "cardinality": {
                "field": field,
                "precision_threshold": _CARDINALITY_PRECISION_THRESHOLD,
            }
        }

    @staticmethod
    def _get_distinct_count(agg: dict, log_count: int) -> DistinctCount:
        return DistinctCount(
            # an approximate count may exceed the number of logs it is computed on
            count=min(agg["value"], log_count),
            approx=agg["value"] > _CARDINALITY_PRECISION_THRESHOLD,
        )

    @classmethod
    def _get_bucket_distinct_count(cls, bucket: dict) -> DistinctCount:
        return cls._get_distinct_count(bucket["distinct"], bucket["doc_count"])

    @staticmethod
    def _get_truncation(buckets: list, cardinality_agg: dict) -> dict:
        """
        Return the total / truncated fields of a TruncatedList / TruncatedDict.
        """
        # the cardinality may be approximate, but it can't be lower than the
        # number of buckets we actually got
        total = max(cardinality_agg["value"], len(buckets))
        return {"total": total, "truncated": total > len(buckets)}

    @staticmethod
    def _es_date_to_datetime(value: float) -> datetime:
        return datetime.fromtimestamp(value / 1000, timezone.utc)

    @classmethod
    def _get_log_dates(cls, aggs: dict) -> dict[str, datetime | None]:
        """
        Return the first_log_at / last_log_at fields of a description.
        """
        if aggs["date_min"]["value"] is None:
            return {"first_log_at": None, "last_log_at": None}
        return {
            "first_log_at": cls._es_date_to_datetime(aggs["date_min"]["value"]),
            "last_log_at": cls._es_date_to_datetime(aggs["date_max"]["value"]),
        }

    @classmethod
    def _build_type_stats_aggregation(
        cls, type_field: str, ref_field: str | None = None
    ) -> dict:
        aggregation = {"terms": {"field": type_field, "size": _MAX_ACTION_TYPES}}
        if ref_field:
            aggregation["aggs"] = {
                "distinct": cls._build_cardinality_aggregation(ref_field)
            }
        return aggregation

    @classmethod
    def _build_common_describe_aggregations(cls) -> dict:
        return {
            "date_min": {"min": {"field": "emitted_at"}},
            "date_max": {"max": {"field": "emitted_at"}},
            "resource_types": cls._build_type_stats_aggregation(
                "resource.type", "resource.ref"
            ),
            "no_resource": {"missing": {"field": "resource.ref"}},
        }

    @classmethod
    def _get_actor_types(cls, agg: dict) -> list[ActorTypeStats]:
        return [
            ActorTypeStats(
                name=bucket["key"],
                logs=bucket["doc_count"],
                distinct_actors=cls._get_bucket_distinct_count(bucket),
            )
            for bucket in agg["buckets"]
        ]

    @classmethod
    def _get_resource_types(cls, agg: dict) -> list[ResourceTypeStats]:
        return [
            ResourceTypeStats(
                name=bucket["key"],
                logs=bucket["doc_count"],
                distinct_resources=cls._get_bucket_distinct_count(bucket),
            )
            for bucket in agg["buckets"]
        ]

    @classmethod
    def _build_custom_field_catalog_aggregations(cls) -> dict:
        aggregations = {}
        for group, path in CUSTOM_FIELD_GROUP_PATHS.items():
            aggregations[group] = {
                "terms": {"field": f"{path}_fields", "size": _MAX_FIELDS_PER_GROUP},
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
            aggregations[f"{group}_total"] = cls._build_cardinality_aggregation(
                f"{path}_fields"
            )
        return aggregations

    @classmethod
    def _build_describe_repo_aggregations(cls) -> dict:
        return {
            **cls._build_common_describe_aggregations(),
            "actions": {
                "terms": {"field": "action.type", "size": _MAX_ACTION_TYPES},
                "aggs": {
                    "category": {"terms": {"field": "action.category", "size": 1}}
                },
            },
            "actions_total": cls._build_cardinality_aggregation("action.type"),
            "actor_types": cls._build_type_stats_aggregation("actor.type", "actor.ref"),
            "no_actor": {"missing": {"field": "actor.ref"}},
            **cls._build_custom_field_catalog_aggregations(),
        }

    @classmethod
    def _get_action_types(cls, aggs: dict) -> TruncatedList[ActionTypeStats]:
        buckets = aggs["actions"]["buckets"]
        return TruncatedList[ActionTypeStats](
            **cls._get_truncation(buckets, aggs["actions_total"]),
            items=[
                ActionTypeStats(
                    name=bucket["key"],
                    # action.category is mandatory, there is always one
                    category=bucket["category"]["buckets"][0]["key"],
                    logs=bucket["doc_count"],
                )
                for bucket in buckets
            ],
        )

    @classmethod
    def _get_custom_field_catalog(
        cls, aggs: dict
    ) -> CustomFieldGroups[TruncatedDict[CustomFieldType]]:
        groups = {}
        for group, path in CUSTOM_FIELD_GROUP_PATHS.items():
            buckets = aggs[group]["buckets"]
            groups[group] = TruncatedDict[CustomFieldType](
                **cls._get_truncation(buckets, aggs[f"{group}_total"]),
                items={
                    bucket["key"]: cls._get_custom_field_type_from_source(
                        bucket["latest"]["hits"]["hits"][0]["_source"],
                        path,
                        bucket["key"],
                    )
                    for bucket in buckets
                },
            )
        return CustomFieldGroups[TruncatedDict[CustomFieldType]](**groups)

    async def describe_repo(
        self,
        *,
        authorized_entities: set[str] = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> RepoDescription:
        resp = await self.es.search(
            index=self.read_alias,
            query=await self._build_es_query(
                LogSearchParams(since=since, until=until),
                authorized_entities=authorized_entities,
            ),
            size=0,
            track_total_hits=True,
            aggregations=self._build_describe_repo_aggregations(),
        )
        aggs = resp["aggregations"]
        return RepoDescription(
            logs=resp["hits"]["total"]["value"],
            **self._get_log_dates(aggs),
            action_types=self._get_action_types(aggs),
            actor_types=self._get_actor_types(aggs["actor_types"]),
            resource_types=self._get_resource_types(aggs["resource_types"]),
            logs_without_actor=aggs["no_actor"]["doc_count"],
            logs_without_resource=aggs["no_resource"]["doc_count"],
            custom_fields=self._get_custom_field_catalog(aggs),
        )

    async def _get_mapped_custom_fields(self) -> list[_MappedCustomField]:
        """
        Return the custom fields known by the index mapping, ordered by group,
        name and type.
        """
        resp = await self.es.indices.get_mapping(index=self.read_alias)
        fields = set()
        # NB: the read alias may point to several indices during a reindex
        for index_mapping in resp.values():
            properties = index_mapping["mappings"].get("properties", {})
            for group, path in CUSTOM_FIELD_GROUP_PATHS.items():
                node = {"properties": properties}
                for key in path.split("."):
                    node = node.get("properties", {}).get(key, {})
                for key in node.get("properties", {}):
                    name, _, field_type = key.rpartition(":")
                    if field_type in CustomFieldType:
                        fields.add(
                            _MappedCustomField(group, name, CustomFieldType(field_type))
                        )
        groups = list(CUSTOM_FIELD_GROUP_PATHS)
        return sorted(
            fields,
            key=lambda field: (groups.index(field.group), field.name, field.type),
        )

    @classmethod
    def _build_custom_field_stats_aggregation(cls, field: _MappedCustomField) -> dict:
        # the date of the last log having the field tells which type is the most
        # recent one when the field has been used with several types
        aggs = {"last_log_at": {"max": {"field": "emitted_at"}}}
        if field.type in AGGREGATABLE_CUSTOM_FIELD_TYPES:
            aggs["distinct"] = cls._build_cardinality_aggregation(field.es_field)
            # one more than the limit to know whether the limit is exceeded
            aggs["values"] = {
                "terms": {"field": field.es_field, "size": _MAX_ENUM_VALUES + 1}
            }
        if field.type in (
            CustomFieldType.INTEGER,
            CustomFieldType.FLOAT,
            CustomFieldType.DATETIME,
        ):
            aggs["min"] = {"min": {"field": field.es_field}}
            aggs["max"] = {"max": {"field": field.es_field}}
        return {"filter": {"exists": {"field": field.es_field}}, "aggs": aggs}

    async def _search_action_description(
        self,
        action_type: str,
        fields: list[_MappedCustomField],
        *,
        authorized_entities: set[str] | None,
        since: datetime | None,
        until: datetime | None,
    ) -> dict:
        # The query only filters on the action type, so that the number of hits
        # tells whether the action type exists, the time window is applied
        # through the "window" filter aggregation
        window_query = await self._build_es_query(
            LogSearchParams(since=since, until=until)
        )
        resp = await self.es.search(
            index=self.read_alias,
            query=await self._build_es_query(
                LogSearchParams(action_type=action_type),
                authorized_entities=authorized_entities,
            ),
            size=0,
            track_total_hits=1,
            aggregations={
                "category": {"terms": {"field": "action.category", "size": 1}},
                "window": {
                    "filter": window_query or {"match_all": {}},
                    "aggs": {
                        **self._build_common_describe_aggregations(),
                        "actors": self._build_cardinality_aggregation("actor.ref"),
                        "actor_types": self._build_type_stats_aggregation("actor.type"),
                        # the aggregation of fields[i] is named "field_<i>", custom
                        # field names are not used as aggregation names since ES
                        # forbids some characters
                        **{
                            f"field_{i}": self._build_custom_field_stats_aggregation(
                                field
                            )
                            for i, field in enumerate(fields)
                        },
                    },
                },
            },
        )
        if resp["hits"]["total"]["value"] == 0:
            raise NotFoundError(
                f"Unknown action type {action_type!r}, call describe_repo to get "
                f"the available action types"
            )
        return resp["aggregations"]

    @classmethod
    def _get_custom_field_stats(
        cls, field_type: CustomFieldType, agg: dict, log_count: int
    ) -> CustomFieldStats:
        values = None
        if "values" in agg and len(agg["values"]["buckets"]) <= _MAX_ENUM_VALUES:
            values = {
                # NB: boolean keys are 1 / 0, key_as_string gives true / false
                bucket.get("key_as_string", str(bucket["key"])): bucket["doc_count"]
                for bucket in agg["values"]["buckets"]
            }

        range_ = None
        if "min" in agg:
            match field_type:
                case CustomFieldType.DATETIME:
                    convert = cls._es_date_to_datetime
                case CustomFieldType.INTEGER:
                    convert = int
                case _:
                    convert = float
            range_ = [convert(agg["min"]["value"]), convert(agg["max"]["value"])]

        return CustomFieldStats(
            type=field_type,
            coverage=round(agg["doc_count"] / log_count, 3),
            distinct_values=(
                cls._get_distinct_count(agg["distinct"], agg["doc_count"])
                if "distinct" in agg
                else None
            ),
            values=values,
            range=range_,
        )

    @classmethod
    def _get_custom_field_stats_groups(
        cls, fields: list[_MappedCustomField], aggs: dict, log_count: int
    ) -> CustomFieldGroups[TruncatedDict[CustomFieldStats]]:
        # Only keep the custom fields actually present in the logs and, for a field
        # used with several types, only its most recent type (as list_*_fields and
        # log filters do)
        latest_fields = {}
        for i, field in enumerate(fields):
            agg = aggs[f"field_{i}"]
            if agg["doc_count"] == 0:
                continue
            key = (field.group, field.name)
            if (
                key not in latest_fields
                or agg["last_log_at"]["value"]
                > latest_fields[key][1]["last_log_at"]["value"]
            ):
                latest_fields[key] = (field, agg)

        stats_by_group = {group: [] for group in CUSTOM_FIELD_GROUP_PATHS}
        for field, agg in latest_fields.values():
            stats_by_group[field.group].append(
                (field.name, cls._get_custom_field_stats(field.type, agg, log_count))
            )

        groups = {}
        for group, stats in stats_by_group.items():
            stats.sort(key=lambda item: (-item[1].coverage, item[0]))
            groups[group] = TruncatedDict[CustomFieldStats](
                total=len(stats),
                truncated=len(stats) > _MAX_FIELDS_PER_GROUP,
                items=dict(stats[:_MAX_FIELDS_PER_GROUP]),
            )
        return CustomFieldGroups[TruncatedDict[CustomFieldStats]](**groups)

    async def describe_action(
        self,
        action_type: str,
        *,
        authorized_entities: set[str] = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ActionDescription:
        fields = await self._get_mapped_custom_fields()
        aggs = await self._search_action_description(
            action_type,
            fields,
            authorized_entities=authorized_entities,
            since=since,
            until=until,
        )
        window_aggs = aggs["window"]
        log_count = window_aggs["doc_count"]
        return ActionDescription(
            action_type=action_type,
            # action.category is mandatory, there is always one
            category=aggs["category"]["buckets"][0]["key"],
            logs=log_count,
            **self._get_log_dates(window_aggs),
            distinct_actors=self._get_distinct_count(window_aggs["actors"], log_count),
            actor_types=[
                TypeLogCount(name=bucket["key"], logs=bucket["doc_count"])
                for bucket in window_aggs["actor_types"]["buckets"]
            ],
            resource_types=self._get_resource_types(window_aggs["resource_types"]),
            logs_without_resource=window_aggs["no_resource"]["doc_count"],
            custom_fields=self._get_custom_field_stats_groups(
                fields, window_aggs, log_count
            ),
        )
