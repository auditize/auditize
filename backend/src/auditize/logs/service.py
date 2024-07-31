import csv
import re
from datetime import datetime, timedelta
from functools import partial
from io import StringIO
from itertools import count
from typing import Any, AsyncGenerator

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.config import get_config
from auditize.database import DatabaseManager
from auditize.exceptions import UnknownModelException, ValidationError
from auditize.helpers.datetime import now, serialize_datetime
from auditize.helpers.pagination.cursor.service import find_paginated_by_cursor
from auditize.helpers.pagination.page.models import PagePaginationInfo
from auditize.helpers.pagination.page.service import find_paginated_by_page
from auditize.helpers.resources.service import (
    create_resource_document,
    delete_resource_document,
    get_resource_document,
    has_resource_document,
    update_resource_document,
)
from auditize.logs.db import (
    LogDatabase,
    get_log_db_for_maintenance,
    get_log_db_for_reading,
    get_log_db_for_writing,
)
from auditize.logs.models import CustomField, Log, Node
from auditize.repos.models import Repo
from auditize.repos.service import get_retention_period_enabled_repos

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
    "attachment_description",
    "node_path:ref",
    "node_path:name",
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


async def consolidate_log_node_path(db: LogDatabase, node_path: list[Log.Node]):
    parent_node_ref = None
    for node in node_path:
        await db.consolidate_data(
            db.log_nodes,
            {"parent_node_ref": parent_node_ref, "ref": node.ref, "name": node.name},
        )
        parent_node_ref = node.ref


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


async def save_log(dbm: DatabaseManager, repo_id: str, log: Log) -> str:
    db = await get_log_db_for_writing(dbm, repo_id)

    log_id = await create_resource_document(db.logs, log)

    await consolidate_log_action(db, log.action)

    await consolidate_log_source(db, log.source)

    if log.actor:
        await consolidate_log_actor(db, log.actor)

    if log.resource:
        await consolidate_log_resource(db, log.resource)

    await consolidate_log_details(db, log.details)

    await consolidate_log_tags(db, log.tags)

    await consolidate_log_node_path(db, log.node_path)

    return log_id


async def save_log_attachment(
    dbm: DatabaseManager,
    repo_id: str,
    log_id: str,
    *,
    name: str,
    description: str | None,
    type: str,
    mime_type: str,
    data: bytes,
):
    db = await get_log_db_for_writing(dbm, repo_id)
    attachment = Log.Attachment(
        name=name, description=description, type=type, mime_type=mime_type, data=data
    )
    await update_resource_document(
        db.logs,
        log_id,
        {"attachments": attachment.model_dump()},
        operator="$push",
    )
    await consolidate_log_attachment(db, attachment)


async def get_log(
    dbm: DatabaseManager, repo_id: str, log_id: str, authorized_nodes: set[str]
) -> Log:
    db = await get_log_db_for_reading(dbm, repo_id)
    filter = {"_id": ObjectId(log_id)}
    if authorized_nodes:
        filter["node_path.ref"] = {"$in": list(authorized_nodes)}
    document = await get_resource_document(
        db.logs,
        filter=filter,
        projection=_EXCLUDE_ATTACHMENT_DATA,
    )
    return Log.model_validate(document)


async def get_log_attachment(
    dbm: DatabaseManager, repo_id: str, log_id: str, attachment_idx: int
) -> Log.Attachment:
    db = await get_log_db_for_reading(dbm, repo_id)
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


async def get_logs(
    dbm: DatabaseManager,
    repo: str | LogDatabase,
    *,
    authorized_nodes: set[str] = None,
    action_type: str = None,
    action_category: str = None,
    actor_type: str = None,
    actor_name: str = None,
    actor_ref: str = None,
    actor_extra: dict = None,
    resource_type: str = None,
    resource_name: str = None,
    resource_ref: str = None,
    resource_extra: dict = None,
    details: dict = None,
    source: dict = None,
    tag_ref: str = None,
    tag_type: str = None,
    tag_name: str = None,
    attachment_name: str = None,
    attachment_description: str = None,
    attachment_type: str = None,
    attachment_mime_type: str = None,
    node_ref: str = None,
    since: datetime = None,
    until: datetime = None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list[Log], str | None]:
    if isinstance(repo, LogDatabase):
        db = repo
    else:
        db = await get_log_db_for_reading(dbm, repo)

    criteria: list[dict[str, Any]] = []
    if authorized_nodes:
        criteria.append({"node_path.ref": {"$in": list(authorized_nodes)}})
    if action_type:
        criteria.append({"action.type": action_type})
    if action_category:
        criteria.append({"action.category": action_category})
    if source:
        criteria.append({"source": _custom_field_search_filter(source)})
    if actor_type:
        criteria.append({"actor.type": actor_type})
    if actor_name:
        criteria.append({"actor.name": _text_search_filter(actor_name)})
    if actor_ref:
        criteria.append({"actor.ref": actor_ref})
    if actor_extra:
        criteria.append({"actor.extra": _custom_field_search_filter(actor_extra)})
    if resource_type:
        criteria.append({"resource.type": resource_type})
    if resource_name:
        criteria.append({"resource.name": _text_search_filter(resource_name)})
    if resource_ref:
        criteria.append({"resource.ref": resource_ref})
    if resource_extra:
        criteria.append({"resource.extra": _custom_field_search_filter(resource_extra)})
    if details:
        criteria.append({"details": _custom_field_search_filter(details)})
    if tag_ref:
        criteria.append({"tags.ref": tag_ref})
    if tag_type:
        criteria.append({"tags.type": tag_type})
    if tag_name:
        criteria.append({"tags.name": _text_search_filter(tag_name)})
    if attachment_name:
        criteria.append({"attachments.name": _text_search_filter(attachment_name)})
    if attachment_description:
        criteria.append(
            {"attachments.description": _text_search_filter(attachment_description)}
        )
    if attachment_type:
        criteria.append({"attachments.type": attachment_type})
    if attachment_mime_type:
        criteria.append({"attachments.mime_type": attachment_mime_type})
    if node_ref:
        criteria.append({"node_path.ref": node_ref})
    if since:
        criteria.append({"saved_at": {"$gte": since}})
    if until:
        # don't want to miss logs saved at the same second, meaning that the "until: ...23:59:59" criterion
        # will also include logs saved at 23:59:59.500 for instance
        criteria.append({"saved_at": {"$lte": until.replace(microsecond=999999)}})

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
    data["attachment_description"] = "|".join(
        attachment.description or "" for attachment in log.attachments
    )
    data["attachment_type"] = "|".join(
        attachment.type for attachment in log.attachments
    )
    data["attachment_mime_type"] = "|".join(
        attachment.mime_type for attachment in log.attachments
    )
    data["node_path:ref"] = " > ".join(node.ref for node in log.node_path)
    data["node_path:name"] = " > ".join(node.name for node in log.node_path)
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
    dbm: DatabaseManager, repo_id: str, *, columns: list[str], **kwargs
) -> AsyncGenerator[str, None]:
    max_rows = get_config().csv_max_rows
    returned_rows = 0
    logs_db = await get_log_db_for_reading(dbm, repo_id)
    cursor = None
    for i in count(0):
        csv_buffer = StringIO()
        csv_writer = csv.DictWriter(
            csv_buffer, fieldnames=columns, extrasaction="ignore"
        )
        if i == 0:
            csv_writer.writeheader()
        logs, cursor = await get_logs(
            dbm,
            logs_db,
            pagination_cursor=cursor,
            limit=min(100, max_rows - returned_rows) if max_rows > 0 else 100,
            **kwargs,
        )
        returned_rows += len(logs)
        csv_writer.writerows(map(_log_to_dict, logs))
        yield csv_buffer.getvalue()
        if not cursor or (max_rows > 0 and returned_rows >= max_rows):
            break


async def _get_consolidated_data_aggregated_field(
    dbm: DatabaseManager,
    repo_id: str,
    collection_name: str,
    field_name: str,
    *,
    match=None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    # Get all unique aggregated data field
    db = await get_log_db_for_reading(dbm, repo_id)
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
    dbm: DatabaseManager,
    repo_id,
    collection_name,
    field_name: str,
    *,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    db = await get_log_db_for_reading(dbm, repo_id)
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
    dbm: DatabaseManager,
    repo_id: str,
    *,
    action_category: str = None,
    page=1,
    page_size=10,
) -> tuple[list[str], PagePaginationInfo]:
    return await _get_consolidated_data_aggregated_field(
        dbm,
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


async def _get_log_nodes(db: LogDatabase, *, match, pipeline_extra=None):
    return db.log_nodes.aggregate(
        [
            {"$match": match},
            {
                "$lookup": {
                    "from": "log_nodes",
                    "let": {"ref": "$ref"},
                    "pipeline": [
                        {"$match": {"$expr": {"$eq": ["$parent_node_ref", "$$ref"]}}},
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


async def _get_node_hierarchy(db: LogDatabase, node_ref: str) -> set[str]:
    node = await _get_log_node(db, node_ref)
    hierarchy = {node.ref}
    while node.parent_node_ref:
        node = await _get_log_node(db, node.parent_node_ref)
        hierarchy.add(node.ref)
    return hierarchy


async def _get_nodes_hierarchy(db: LogDatabase, node_refs: set[str]) -> set[str]:
    parent_nodes: dict[str, str] = {}
    for node_ref in node_refs:
        node = await _get_log_node(db, node_ref)
        while True:
            if node.ref in parent_nodes:
                break
            parent_nodes[node.ref] = node.parent_node_ref
            if not node.parent_node_ref:
                break
            node = await _get_log_node(db, node.parent_node_ref)

    return node_refs | parent_nodes.keys()


async def get_log_nodes(
    dbm: DatabaseManager,
    repo_id: str,
    authorized_nodes: set[str],
    *,
    parent_node_ref=NotImplemented,
    page=1,
    page_size=10,
) -> tuple[list[Log.Node], PagePaginationInfo]:
    db = await get_log_db_for_reading(dbm, repo_id)

    # please note that we use NotImplemented instead of None because None is a valid value for parent_node_ref
    # (it means filtering on top nodes)
    if parent_node_ref is NotImplemented:
        filter = {}
    else:
        filter = {"parent_node_ref": parent_node_ref}

    if authorized_nodes:
        # get the complete hierarchy of the node from the node itself to the top node
        parent_node_ref_hierarchy = (
            await _get_node_hierarchy(db, parent_node_ref) if parent_node_ref else set()
        )
        # we check if we have permission on parent_node_ref or any of its parent nodes
        # if not, we have to manually filter the nodes we'll have a direct or indirect visibility
        if not parent_node_ref_hierarchy or not (
            authorized_nodes & parent_node_ref_hierarchy
        ):
            visible_nodes = await _get_nodes_hierarchy(db, authorized_nodes)
            filter["ref"] = {"$in": list(visible_nodes)}

    results = await _get_log_nodes(
        db,
        match=filter,
        pipeline_extra=[
            {"$sort": {"name": 1}},
            {"$skip": (page - 1) * page_size},
            {"$limit": page_size},
        ],
    )

    total = await db.log_nodes.count_documents(filter or {})

    return (
        [Node(**result) async for result in results],
        PagePaginationInfo.build(page=page, page_size=page_size, total=total),
    )


async def _get_log_node(db: LogDatabase, node_ref: str) -> Log.Node:
    results = await (await _get_log_nodes(db, match={"ref": node_ref})).to_list(None)
    try:
        result = results[0]
    except IndexError:
        raise UnknownModelException(node_ref)

    return Node(**result)


async def get_log_node(
    dbm: DatabaseManager, repo_id: str, node_ref: str, authorized_nodes: set[str]
) -> Log.Node:
    db = await get_log_db_for_reading(dbm, repo_id)
    if authorized_nodes:
        node_ref_hierarchy = await _get_node_hierarchy(db, node_ref)
        authorized_nodes_hierarchy = await _get_nodes_hierarchy(db, authorized_nodes)
        if not (
            node_ref_hierarchy & authorized_nodes
            or node_ref in authorized_nodes_hierarchy
        ):
            raise UnknownModelException()
    return await _get_log_node(db, node_ref)


async def _apply_log_retention_period(dbm: DatabaseManager, repo: Repo):
    if not repo.retention_period:
        return

    db = await get_log_db_for_maintenance(dbm, repo.id)
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
                f"{doc!r} from log repository {db.repo.name!r}"
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


async def _purge_orphan_consolidated_log_node_if_needed(db: LogDatabase, node: Node):
    """
    This function assumes that the node has no children and delete it if it has no associated logs.
    It performs the same operation recursively on its ancestors.
    """
    has_associated_logs = await has_resource_document(
        db.logs, {"node_path.ref": node.ref}
    )
    if not has_associated_logs:
        await delete_resource_document(db.log_nodes, node.id)
        print(f"Deleted orphan log node {node!r} from log repository {db.repo.name!r}")
        if node.parent_node_ref:
            parent_node = await _get_log_node(db, node.parent_node_ref)
            if not parent_node.has_children:
                await _purge_orphan_consolidated_log_node_if_needed(db, parent_node)


async def _purge_orphan_consolidated_log_nodes(db: LogDatabase):
    docs = await _get_log_nodes(
        db, match={}, pipeline_extra=[{"$match": {"has_children": False}}]
    )
    async for doc in docs:
        node = Node.model_validate(doc)
        await _purge_orphan_consolidated_log_node_if_needed(db, node)


async def _purge_orphan_consolidated_log_data(dbm: DatabaseManager, repo: Repo):
    db = await get_log_db_for_maintenance(dbm, repo.id)
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
    await _purge_orphan_consolidated_log_nodes(db)


async def apply_log_retention_period(dbm: DatabaseManager):
    for repo in await get_retention_period_enabled_repos(dbm):
        await _apply_log_retention_period(dbm, repo)
        await _purge_orphan_consolidated_log_data(dbm, repo)
