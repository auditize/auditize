from functools import partial
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.exceptions import (
    ConstraintViolation,
    UnknownModelException,
)
from auditize.log.db import (
    LogDatabase,
    get_log_db_for_maintenance,
    get_log_db_for_reading,
)
from auditize.log.models import CustomField, Entity, Log
from auditize.repo.models import Repo
from auditize.resource.pagination.page.models import PagePaginationInfo
from auditize.resource.pagination.page.service import find_paginated_by_page
from auditize.resource.service import (
    delete_resource_document,
    has_resource_document,
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


async def consolidate_log(db: LogDatabase, log: Log):
    await consolidate_log_action(db, log.action)
    await consolidate_log_source(db, log.source)
    if log.actor:
        await consolidate_log_actor(db, log.actor)
    if log.resource:
        await consolidate_log_resource(db, log.resource)
    await consolidate_log_details(db, log.details)
    await consolidate_log_tags(db, log.tags)
    await consolidate_log_entity_path(db, log.entity_path)


async def check_log(db: LogDatabase, log: Log):
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
                f"the same entity name but with another ref at the same level (same parent)"
            )
        parent_entity_ref = entity.ref


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


async def purge_orphan_consolidated_log_data(repo: Repo):
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
