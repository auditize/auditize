import csv
import re
from datetime import timedelta
from functools import partial
from io import StringIO
from itertools import count
from typing import Any, AsyncGenerator
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.config import get_config
from auditize.exceptions import (
    ConstraintViolation,
    UnknownModelException,
    ValidationError,
)
from auditize.helpers.datetime import now, serialize_datetime
from auditize.log.db import (
    LogDatabase,
    get_log_db_for_maintenance,
    get_log_db_for_reading,
    get_log_db_for_writing,
)
from auditize.log.models import CustomField, Log, LogSearchParams, Entity
from auditize.repo.models import Repo
from auditize.repo.service import get_retention_period_enabled_repos
from auditize.resource.pagination.cursor.service import find_paginated_by_cursor
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    has_resource_document,
    update_resource_document,
)

# Exclude attachments data as they can be large and are not mapped in the AttachmentMetadata model
_EXCLUDE_ATTACHMENT_DATA = {"attachments.data": 0}

CSV_BUILTIN_COLUMNS = (
    "log_id",
    "saved_at",
    "action_type",
    "action_category",
    "actor_ref",
    "actor_type",
    "actor_name",
    "resource_ref",
    "resource_type",
    "resource_name",
    "tag_ref",
    "tag_type",
    "tag_name",
    "attachment_name",
    "attachment_type",
    "attachment_mime_type",
    "entity_path:ref",
    "entity_path:name",
)


async def consolidate_log_action(db: LogDatabase, action: Log.Action):
    await db.consolidate_data(
        db.log_actions, {"category": action.category, "type": action.type}
    )


async def consolidate_log_source(db: LogDatabase, source: list[CustomField]):
    for field in source:
        await db.consolidate_data(db.log_source_fields, {"name": field.name})


async def consolidate_log_actor(db: LogDatabase, actor: Log.Actor):
    await db.consolidate_data(db.log_actor_types, {"type": actor.type})
    for field in actor.extra:
        await db.consolidate_data(db.log_actor_extra_fields, {"name": field.name})


async def consolidate_log_resource(db: LogDatabase, resource: Log.Resource):
    await db.consolidate_data(db.log_resource_types, {"type": resource.type})
    for field in resource.extra:
        await db.consolidate_data(db.log_resource_extra_fields, {"name": field.name})


async def consolidate_log_tags(db: LogDatabase, tags: list[Log.Tag]):
    for tag in tags:
        await db.consolidate_data(db.log_tag_types, {"type": tag.type})


async def consolidate_log_details(db: LogDatabase, details: list[CustomField]):
    for field in details:
        await db.consolidate_data(db.log_detail_fields, {"name": field.name})


async def consolidate_log_entity_path(db: LogDatabase, entity_path: list[Log.Entity]):
    parent_entity_ref = None
    for entity in entity_path:
        await db.consolidate_data(
            db.log_entities,
            {"ref": entity.ref},
            {"parent_entity_ref": parent_entity_ref, "name": entity.name},
        )
        parent_entity_ref = entity.ref


async def consolidate_log_attachment(
    db: LogDatabase, attachment: Log.AttachmentMetadata
):
    await db.consolidate_data(
        db.log_attachment_types,
        {
            "type": attachment.type,
        },
    )
    await db.consolidate_data(
        db.log_attachment_mime_types,
        {
            "mime_type": attachment.mime_type,
        },
    )


async def _consolidate_log(db: LogDatabase, log: Log):
    await consolidate_log_action(db, log.action)
    await consolidate_log_source(db, log.source)
    if log.actor:
        await consolidate_log_actor(db, log.actor)
    if log.resource:
        await consolidate_log_resource(db, log.resource)
    await consolidate_log_details(db, log.details)
    await consolidate_log_tags(db, log.tags)
    await consolidate_log_entity_path(db, log.entity_path)


async def _check_log(db: LogDatabase, log: Log):
    parent_entity_ref = None
    for entity in log.entity_path:
        if await has_resource_document(
            db.log_entities,
            {
                "parent_entity_ref": parent_entity_ref,
                "name": entity.name,
                "ref": {"$ne": entity.ref},
            },
        ):
            raise ConstraintViolation(
                f"Entity {entity.ref!r} is invalid, there are other logs with "
                f"the same entity name at the same level (same parent)"
            )
        parent_entity_ref = entity.ref


async def save_log(repo_id: UUID, log: Log) -> UUID:
    db = await get_log_db_for_writing(repo_id)

    await _check_log(db, log)
    log_id = await create_resource_document(db.logs, log)

    await _consolidate_log(db, log)

    return log_id


async def save_log_attachment(
    repo_id: UUID,
    log_id: UUID,
    *,
    name: str,
    type: str,
    mime_type: str,
    data: bytes,
):
    db = await get_log_db_for_writing(repo_id)
    attachment = Log.Attachment(name=name, type=type, mime_type=mime_type, data=data)
    await update_resource_document(
        db.logs,
        log_id,
        {"attachments": attachment.model_dump()},
        operator="$push",
    )
    await consolidate_log_attachment(db, attachment)


async def get_log(repo_id: UUID, log_id: UUID, authorized_entities: set[str]) -> Log:
    db = await get_log_db_for_reading(repo_id)
    filter = {"_id": log_id}
    if authorized_entities:
        filter["entity_path.ref"] = {"$in": list(authorized_entities)}
    document = await get_resource_document(
        db.logs,
        filter=filter,
        projection=_EXCLUDE_ATTACHMENT_DATA,
    )
    return Log.model_validate(document)


async def get_log_attachment(
    repo_id: UUID, log_id: UUID, attachment_idx: int
) -> Log.Attachment:
    db = await get_log_db_for_reading(repo_id)
    doc = await get_resource_document(
        db.logs, log_id, projection={"attachments": {"$slice": [attachment_idx, 1]}}
    )
    if len(doc["attachments"]) == 0:
        raise UnknownModelException()
    return Log.Attachment(**doc["attachments"][0])


def _text_search_filter(text: str) -> dict[str, Any]:
    return {"$regex": re.compile(re.escape(text), re.IGNORECASE)}


def _custom_field_search_filter(params: dict[str, str]) -> dict:
    return {
        "$all": [
            {"$elemMatch": {"name": name, "value": _text_search_filter(value)}}
            for name, value in params.items()
        ]
    }


def _get_criteria_from_search_params(
    search_params: LogSearchParams,
) -> list[dict[str, Any]]:
    sp = search_params
    criteria = []
    if sp.action_type:
        criteria.append({"action.type": sp.action_type})
    if sp.action_category:
        criteria.append({"action.category": sp.action_category})
    if sp.source:
        criteria.append({"source": _custom_field_search_filter(sp.source)})
    if sp.actor_type:
        criteria.append({"actor.type": sp.actor_type})
    if sp.actor_name:
        criteria.append({"actor.name": _text_search_filter(sp.actor_name)})
    if sp.actor_ref:
        criteria.append({"actor.ref": sp.actor_ref})
    if sp.actor_extra:
        criteria.append({"actor.extra": _custom_field_search_filter(sp.actor_extra)})
    if sp.resource_type:
        criteria.append({"resource.type": sp.resource_type})
    if sp.resource_name:
        criteria.append({"resource.name": _text_search_filter(sp.resource_name)})
    if sp.resource_ref:
        criteria.append({"resource.ref": sp.resource_ref})
    if sp.resource_extra:
        criteria.append(
            {"resource.extra": _custom_field_search_filter(sp.resource_extra)}
        )
    if sp.details:
        criteria.append({"details": _custom_field_search_filter(sp.details)})
    if sp.tag_ref:
        criteria.append({"tags.ref": sp.tag_ref})
    if sp.tag_type:
        criteria.append({"tags.type": sp.tag_type})
    if sp.tag_name:
        criteria.append({"tags.name": _text_search_filter(sp.tag_name)})
    if sp.has_attachment is not None:
        if sp.has_attachment:
            criteria.append({"attachments": {"$not": {"$size": 0}}})
        else:
            criteria.append({"attachments": {"$size": 0}})
    if sp.attachment_name:
        criteria.append({"attachments.name": _text_search_filter(sp.attachment_name)})
    if sp.attachment_type:
        criteria.append({"attachments.type": sp.attachment_type})
    if sp.attachment_mime_type:
        criteria.append({"attachments.mime_type": sp.attachment_mime_type})
    if sp.entity_ref:
        criteria.append({"entity_path.ref": sp.entity_ref})
    if sp.since:
        criteria.append({"saved_at": {"$gte": sp.since}})
    if sp.until:
        # don't want to miss logs saved at the same second, meaning that the "until: ...23:59:59" criterion
        # will also include logs saved at 23:59:59.500 for instance
        criteria.append({"saved_at": {"$lte": sp.until.replace(microsecond=999999)}})
    return criteria


async def get_logs(
    repo: UUID | LogDatabase,
    *,
    authorized_entities: set[str] = None,
    search_params: LogSearchParams = None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list[Log], str | None]:
    if isinstance(repo, LogDatabase):
        db = repo
    else:
        db = await get_log_db_for_reading(repo)

    criteria: list[dict[str, Any]] = []
    if authorized_entities:
        criteria.append({"entity_path.ref": {"$in": list(authorized_entities)}})
    if search_params:
        criteria.extend(_get_criteria_from_search_params(search_params))

    results, next_cursor = await find_paginated_by_cursor(
        db.logs,
        id_field="_id",
        date_field="saved_at",
        projection=_EXCLUDE_ATTACHMENT_DATA,
        filter={"$and": criteria} if criteria else None,
        limit=limit,
        pagination_cursor=pagination_cursor,
    )

    logs = [Log(**result) for result in results]

    return logs, next_cursor


def _custom_fields_to_dict(custom_fields: list[CustomField], prefix: str) -> dict:
    return {f"{prefix}.{field.name}": field.value for field in custom_fields}


def _log_to_dict(log: Log) -> dict[str, Any]:
    data = dict()
    data["log_id"] = str(log.id)
    data["action_category"] = log.action.category
    data["action_type"] = log.action.type
    data.update(_custom_fields_to_dict(log.source, "source"))
    if log.actor:
        data["actor_type"] = log.actor.type
        data["actor_name"] = log.actor.name
        data["actor_ref"] = log.actor.ref
        data.update(_custom_fields_to_dict(log.actor.extra, "actor"))
    if log.resource:
        data["resource_type"] = log.resource.type
        data["resource_name"] = log.resource.name
        data["resource_ref"] = log.resource.ref
        data.update(_custom_fields_to_dict(log.resource.extra, "resource"))
    data.update(_custom_fields_to_dict(log.details, "details"))
    data["tag_ref"] = "|".join(tag.ref or "" for tag in log.tags)
    data["tag_type"] = "|".join(tag.type for tag in log.tags)
    data["tag_name"] = "|".join(tag.name or "" for tag in log.tags)
    data["attachment_name"] = "|".join(
        attachment.name for attachment in log.attachments
    )
    data["attachment_type"] = "|".join(
        attachment.type for attachment in log.attachments
    )
    data["attachment_mime_type"] = "|".join(
        attachment.mime_type for attachment in log.attachments
    )
    data["entity_path:ref"] = " > ".join(entity.ref for entity in log.entity_path)
    data["entity_path:name"] = " > ".join(entity.name for entity in log.entity_path)
    data["saved_at"] = serialize_datetime(log.saved_at)

    return data


def validate_csv_columns(cols: list[str]):
    for col in cols:
        if col in CSV_BUILTIN_COLUMNS:
            continue

        parts = col.split(".")
        if len(parts) == 2 and parts[0] in ("source", "actor", "resource", "details"):
            continue

        raise ValidationError(f"Invalid column name: {col!r}")

    if len(cols) != len(set(cols)):
        raise ValidationError("Duplicated column names are forbidden")


async def get_logs_as_csv(
    repo_id: UUID,
    *,
    authorized_entities: set[str] = None,
    search_params: LogSearchParams = None,
    columns: list[str],
) -> AsyncGenerator[str, None]:
    max_rows = get_config().csv_max_rows
    returned_rows = 0
    logs_db = await get_log_db_for_reading(repo_id)
    cursor = None
    for i in count(0):
        csv_buffer = StringIO()
        csv_writer = csv.DictWriter(
            csv_buffer, fieldnames=columns, extrasaction="ignore"
        )
        if i == 0:
            csv_writer.writeheader()
        logs, cursor = await get_logs(
            logs_db,
            authorized_entities=authorized_entities,
            search_params=search_params,
            pagination_cursor=cursor,
            limit=min(100, max_rows - returned_rows) if max_rows > 0 else 100,
        )
        returned_rows += len(logs)
        csv_writer.writerows(map(_log_to_dict, logs))
        yield csv_buffer.getvalue()
        if not cursor or (max_rows > 0 and returned_rows >= max_rows):
            break


async def _get_consolidated_data_aggregated_field(
    repo_id: str,
    collection_name: str,
    field_name: str,
    *,
    match=None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    # Get all unique aggregated data field
    db = await get_log_db_for_reading(repo_id)
    collection = db.get_collection(collection_name)
    results = collection.aggregate(
        ([{"$match": match}] if match else [])
        + [
            {"$group": {"_id": "$" + field_name}},
            {"$sort": {"_id": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
        ]
    )
    values = [result["_id"] async for result in results]

    # Get the total number of unique aggregated field value
    results = collection.aggregate(
        ([{"$match": match}] if match else [])
        + [{"$group": {"_id": "$" + field_name}}, {"$count": "total"}]
    )
    try:
        total = (await results.next())["total"]
    except StopAsyncIteration:
        total = 0

    return values, PagePaginationInfo.build(page=page, page_size=page_size, total=total)


async def _get_consolidated_data_field(
    repo_id,
    collection_name,
    field_name: str,
    *,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_log_db_for_reading(repo_id)
    results, pagination = await find_paginated_by_page(
        db.get_collection(collection_name),
        projection=[field_name],
        sort={field_name: 1},
        page=page,
        page_size=page_size,
    )
    return [result[field_name] async for result in results], pagination


get_log_action_categories = partial(
    _get_consolidated_data_aggregated_field,
    collection_name="log_actions",
    field_name="category",
)


async def get_log_action_types(
    repo_id: str,
    *,
    action_category: str = None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    return await _get_consolidated_data_aggregated_field(
        repo_id,
        collection_name="log_actions",
        field_name="type",
        page=page,
        page_size=page_size,
        match={"category": action_category} if action_category else None,
    )


get_log_actor_types = partial(
    _get_consolidated_data_field,
    collection_name="log_actor_types",
    field_name="type",
)

get_log_actor_extra_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_actor_extra_fields",
    field_name="name",
)

get_log_resource_types = partial(
    _get_consolidated_data_field,
    collection_name="log_resource_types",
    field_name="type",
)

get_log_resource_extra_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_resource_extra_fields",
    field_name="name",
)

get_log_tag_types = partial(
    _get_consolidated_data_field,
    collection_name="log_tag_types",
    field_name="type",
)

get_log_source_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_source_fields",
    field_name="name",
)

get_log_detail_fields = partial(
    _get_consolidated_data_field,
    collection_name="log_detail_fields",
    field_name="name",
)

get_log_attachment_types = partial(
    _get_consolidated_data_field,
    collection_name="log_attachment_types",
    field_name="type",
)

get_log_attachment_mime_types = partial(
    _get_consolidated_data_field,
    collection_name="log_attachment_mime_types",
    field_name="mime_type",
)


async def _get_log_entities(db: LogDatabase, *, match, pipeline_extra=None):
    return db.log_entities.aggregate(
        [
            {"$match": match},
            {
                "$lookup": {
                    "from": "log_entities",
                    "let": {"ref": "$ref"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$parent_entity_ref", "$$ref"]}}},
                        {"$limit": 1},
                    ],
                    "as": "first_child_if_any",
                }
            },
            {
                "$addFields": {
                    "has_children": {"$eq": [{"$size": "$first_child_if_any"}, 1]}
                }
            },
        ]
        + (pipeline_extra or [])
    )


async def _get_entity_hierarchy(db: LogDatabase, entity_ref: str) -> set[str]:
    entity = await _get_log_entity(db, entity_ref)
    hierarchy = {entity.ref}
    while entity.parent_entity_ref:
        entity = await _get_log_entity(db, entity.parent_entity_ref)
        hierarchy.add(entity.ref)
    return hierarchy


async def _get_entities_hierarchy(db: LogDatabase, entity_refs: set[str]) -> set[str]:
    parent_entities: dict[str, str] = {}
    for entity_ref in entity_refs:
        entity = await _get_log_entity(db, entity_ref)
        while True:
            if entity.ref in parent_entities:
                break
            parent_entities[entity.ref] = entity.parent_entity_ref
            if not entity.parent_entity_ref:
                break
            entity = await _get_log_entity(db, entity.parent_entity_ref)

    return entity_refs | parent_entities.keys()


async def get_log_entities(
    repo_id: UUID,
    authorized_entities: set[str],
    *,
    parent_entity_ref=NotImplemented,
    page=1,
    page_size=10,
) -> tuple[list[Log.Entity], PagePaginationInfo]:
    db = await get_log_db_for_reading(repo_id)

    # please note that we use NotImplemented instead of None because None is a valid value for parent_entity_ref
    # (it means filtering on top entities)
    if parent_entity_ref is NotImplemented:
        filter = {}
    else:
        filter = {"parent_entity_ref": parent_entity_ref}

    if authorized_entities:
        # get the complete hierarchy of the entity from the entity itself to the top entity
        parent_entity_ref_hierarchy = (
            await _get_entity_hierarchy(db, parent_entity_ref)
            if parent_entity_ref
            else set()
        )
        # we check if we have permission on parent_entity_ref or any of its parent entities
        # if not, we have to manually filter the entities we'll have a direct or indirect visibility
        if not parent_entity_ref_hierarchy or not (
            authorized_entities & parent_entity_ref_hierarchy
        ):
            visible_entities = await _get_entities_hierarchy(db, authorized_entities)
            filter["ref"] = {"$in": list(visible_entities)}

    results = await _get_log_entities(
        db,
        match=filter,
        pipeline_extra=[
            {"$sort": {"name": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
        ],
    )

    total = await db.log_entities.count_documents(filter or {})

    return (
        [Entity(**result) async for result in results],
        PagePaginationInfo.build(page=page, page_size=page_size, total=total),
    )


async def _get_log_entity(db: LogDatabase, entity_ref: str) -> Log.Entity:
    results = await (await _get_log_entities(db, match={"ref": entity_ref})).to_list(
        None
    )
    try:
        result = results[0]
    except IndexError:
        raise UnknownModelException(entity_ref)

    return Entity(**result)


async def get_log_entity(
    repo_id: UUID, entity_ref: str, authorized_entities: set[str]
) -> Log.Entity:
    db = await get_log_db_for_reading(repo_id)
    if authorized_entities:
        entity_ref_hierarchy = await _get_entity_hierarchy(db, entity_ref)
        authorized_entities_hierarchy = await _get_entities_hierarchy(
            db, authorized_entities
        )
        if not (
            entity_ref_hierarchy & authorized_entities
            or entity_ref in authorized_entities_hierarchy
        ):
            raise UnknownModelException()
    return await _get_log_entity(db, entity_ref)


async def _apply_log_retention_period(repo: Repo):
    if not repo.retention_period:
        return

    db = await get_log_db_for_maintenance(repo.id)
    result = await db.logs.delete_many(
        {"saved_at": {"$lt": now() - timedelta(days=repo.retention_period)}}
    )
    if result.deleted_count > 0:
        print(
            f"Deleted {result.deleted_count} logs older than {repo.retention_period} days "
            f"from log repository {repo.name!r}"
        )


async def _purge_orphan_consolidated_data_collection(
    db: LogDatabase, collection: AsyncIOMotorCollection, filter: callable
):
    docs = collection.find({})
    async for doc in docs:
        has_associated_logs = await has_resource_document(
            db.logs,
            filter(doc),
        )
        if not has_associated_logs:
            await collection.delete_one({"_id": doc["_id"]})
            print(
                f"Deleted orphan consolidated {collection.name} item "
                f"{doc!r} from log repository {db.name!r}"
            )


async def _purge_orphan_consolidated_log_actions(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_actions,
        lambda data: {"action.type": data["type"], "action.category": data["category"]},
    )


async def _purge_orphan_consolidated_log_source_fields(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_source_fields,
        lambda data: {"source.name": data["name"]},
    )


async def _purge_orphan_consolidated_log_actor_types(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_actor_types,
        lambda data: {"actor.type": data["type"]},
    )


async def _purge_orphan_consolidated_log_actor_custom_fields(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_actor_extra_fields,
        lambda data: {"actor.extra.name": data["name"]},
    )


async def _purge_orphan_consolidated_log_resource_types(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_resource_types,
        lambda data: {"resource.type": data["type"]},
    )


async def _purge_orphan_consolidated_log_resource_custom_fields(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_resource_extra_fields,
        lambda data: {"resource.extra.name": data["name"]},
    )


async def _purge_orphan_consolidated_log_tag_types(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_tag_types,
        lambda data: {"tags.type": data["type"]},
    )


async def _purge_orphan_consolidated_log_detail_fields(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_detail_fields,
        lambda data: {"details.name": data["name"]},
    )


async def _purge_orphan_consolidated_log_attachment_types(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_attachment_types,
        lambda data: {"attachments.type": data["type"]},
    )


async def _purge_orphan_consolidated_log_attachment_mime_types(db: LogDatabase):
    await _purge_orphan_consolidated_data_collection(
        db,
        db.log_attachment_mime_types,
        lambda data: {"attachments.mime_type": data["mime_type"]},
    )


async def _purge_orphan_consolidated_log_entity_if_needed(
    db: LogDatabase, entity: Entity
):
    """
    This function assumes that the entity has no children and delete it if it has no associated logs.
    It performs the same operation recursively on its ancestors.
    """
    has_associated_logs = await has_resource_document(
        db.logs, {"entity_path.ref": entity.ref}
    )
    if not has_associated_logs:
        await delete_resource_document(db.log_entities, entity.id)
        print(f"Deleted orphan log entity {entity!r} from log repository {db.name!r}")
        if entity.parent_entity_ref:
            parent_entity = await _get_log_entity(db, entity.parent_entity_ref)
            if not parent_entity.has_children:
                await _purge_orphan_consolidated_log_entity_if_needed(db, parent_entity)


async def _purge_orphan_consolidated_log_entities(db: LogDatabase):
    docs = await _get_log_entities(
        db, match={}, pipeline_extra=[{"$match": {"has_children": False}}]
    )
    async for doc in docs:
        entity = Entity.model_validate(doc)
        await _purge_orphan_consolidated_log_entity_if_needed(db, entity)


async def _purge_orphan_consolidated_log_data(repo: Repo):
    db = await get_log_db_for_maintenance(repo.id)
    await _purge_orphan_consolidated_log_actions(db)
    await _purge_orphan_consolidated_log_source_fields(db)
    await _purge_orphan_consolidated_log_actor_types(db)
    await _purge_orphan_consolidated_log_actor_custom_fields(db)
    await _purge_orphan_consolidated_log_resource_types(db)
    await _purge_orphan_consolidated_log_resource_custom_fields(db)
    await _purge_orphan_consolidated_log_tag_types(db)
    await _purge_orphan_consolidated_log_detail_fields(db)
    await _purge_orphan_consolidated_log_attachment_types(db)
    await _purge_orphan_consolidated_log_attachment_mime_types(db)
    await _purge_orphan_consolidated_log_entities(db)


async def apply_log_retention_period():
    for repo in await get_retention_period_enabled_repos():
        await _apply_log_retention_period(repo)
        await _purge_orphan_consolidated_log_data(repo)
