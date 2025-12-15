from datetime import datetime, timedelta
from uuid import UUID

import pytest

from auditize.database.dbm import open_db_session
from auditize.log.models import Emitter, EmitterType, LogCreate
from auditize.log.service import LogService
from conftest import RepoBuilder
from helpers.http import HttpTestHelper
from helpers.log import UNKNOWN_UUID, PreparedLog
from helpers.repo import PreparedRepo

pytestmark = pytest.mark.anyio


def make_log_data(**extra) -> LogCreate:
    """
    By default, the log data is minimal viable.
    """

    return LogCreate.model_validate(
        {
            "action": {"type": "login", "category": "authentication"},
            "actor": {"type": "user", "ref": "user:123", "name": "User 123"},
            "resource": {"ref": "core", "type": "module", "name": "Core Module"},
            "tags": [{"type": "simple_tag"}],
            "entity_path": [{"ref": "1", "name": "Customer 1"}],
            **extra,
        }
    )


async def test_save_log_db_shape(repo: PreparedRepo):
    log = make_log_data()

    async with open_db_session() as session:
        log_service = await LogService.for_writing(session, UUID(repo.id))
        log = await log_service.create_log(
            log,
            emitter=Emitter(type=EmitterType.APIKEY, id=UNKNOWN_UUID, name="API Key"),
        )
    db_log = await repo.get_log(log.id)
    assert set(db_log.keys()) == {
        "log_id",
        "action",
        "saved_at",
        "source",
        "actor",
        "resource",
        "details",
        "tags",
        "attachments",
        "entity_path",
        "emitter",
    }
    assert db_log["action"].keys() == {"type", "category"}
    assert db_log["actor"].keys() == {"ref", "type", "name", "extra"}
    assert db_log["resource"].keys() == {"ref", "type", "name", "extra"}
    assert db_log["tags"][0].keys() == {"ref", "type", "name"}
    assert db_log["entity_path"][0].keys() == {"ref", "name"}


async def test_log_retention_period_disabled(
    superadmin_client: HttpTestHelper, repo: PreparedRepo
):
    await repo.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=3650)
    )

    async with open_db_session() as session:
        await LogService.apply_log_retention_period(session)
    assert await repo.get_log_count() == 1


async def test_log_retention_period_enabled(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    # we test with repos:
    # - repo_1 with retention period and 1 log that must be deleted and 1 log that must be kept
    # - repo_2 without retention period and 2 logs that must be kept

    repo_1 = await repo_builder({"retention_period": 30})
    repo_1_log_1 = await repo_1.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=31)
    )
    repo_1_log_2 = await repo_1.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=29)
    )

    repo_2 = await repo_builder({})
    repo_2_log_1 = await repo_2.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=31)
    )
    repo_2_log_2 = await repo_2.create_log(
        superadmin_client, saved_at=datetime.now() - timedelta(days=29)
    )

    async with open_db_session() as session:
        await LogService.apply_log_retention_period(session)

    assert await repo_1.get_log_count() == 1
    assert await repo_1.get_log(repo_1_log_2.id) is not None

    assert await repo_2.get_log_count() == 2


async def test_log_retention_period_purge_consolidated_data(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo = await repo_builder({"retention_period": 30})
    log_1 = await repo.create_log(
        superadmin_client,
        data=PreparedLog.prepare_data(
            {
                "action": {"category": "category", "type": "action_type_to_be_kept"},
                "source": [{"name": "source_field_to_be_kept", "value": "value"}],
                "actor": {
                    "name": "some actor",
                    "ref": "actor:123",
                    "type": "actor_type_to_be_kept",
                    "extra": [
                        {"name": "actor_extra_field_to_be_kept", "value": "value"}
                    ],
                },
                "resource": {
                    "name": "some resource",
                    "ref": "resource:123",
                    "type": "resource_type_to_be_kept",
                    "extra": [
                        {"name": "resource_extra_field_to_be_kept", "value": "value"}
                    ],
                },
                "tags": [{"type": "tag_type_to_be_kept"}],
                "details": [{"name": "detail_field_to_be_kept", "value": "value"}],
            }
        ),
        saved_at=datetime.now() - timedelta(days=10),
    )
    await log_1.upload_attachment(
        superadmin_client,
        name="file.txt",
        data=b"hello",
        type="attachment_type_to_be_kept",
        mime_type="mime-type/to-be-kept",
    )
    log_2 = await repo.create_log(
        superadmin_client,
        data=PreparedLog.prepare_data(
            {
                "action": {"category": "category", "type": "action_type_to_be_purged"},
                "source": [{"name": "source_field_to_be_purged", "value": "value"}],
                "actor": {
                    "name": "some other actor",
                    "ref": "actor:456",
                    "type": "actor_type_to_be_purged",
                    "extra": [
                        {"name": "actor_extra_field_to_be_purged", "value": "value"}
                    ],
                },
                "resource": {
                    "name": "some other resource",
                    "ref": "resource:456",
                    "type": "resource_type_to_be_purged",
                    "extra": [
                        {"name": "resource_extra_field_to_be_purged", "value": "value"}
                    ],
                },
                "tags": [{"type": "tag_type_to_be_purged"}],
                "details": [{"name": "detail_field_to_be_purged", "value": "value"}],
            }
        ),
        saved_at=datetime.now() - timedelta(days=40),
    )
    await log_2.upload_attachment(
        superadmin_client,
        name="file.txt",
        data=b"hello",
        type="attachment_type_to_be_purged",
        mime_type="mime-type/to-be-purged",
    )

    async with open_db_session() as session:
        await LogService.apply_log_retention_period(session)


async def test_log_retention_period_purge_log_entities_1(
    superadmin_client: HttpTestHelper, repo_builder: RepoBuilder
):
    repo = await repo_builder({"retention_period": 30})
    # We have the following log entity hierarchy:
    # - A
    #   - AA
    #     - AAA
    #   - AB
    #     - ABA
    #   - AC
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AA", "AAA"],
        saved_at=datetime.now() - timedelta(days=40),
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AB", "ABA"],
        saved_at=datetime.now() - timedelta(days=40),
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AB"],
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AC"],
    )

    async with open_db_session() as session:
        await LogService.apply_log_retention_period(session)

    resp = await superadmin_client.assert_get_ok(f"/repos/{repo.id}/logs/entities")
    assert resp.json() == {
        "items": [
            {"ref": "A", "name": "A", "parent_entity_ref": None, "has_children": True},
            {
                "ref": "AB",
                "name": "AB",
                "parent_entity_ref": "A",
                "has_children": False,
            },
            {
                "ref": "AC",
                "name": "AC",
                "parent_entity_ref": "A",
                "has_children": False,
            },
        ],
        "pagination": {
            "next_cursor": None,
        },
    }


async def test_log_retention_period_purge_log_entities_2(
    superadmin_client: HttpTestHelper,
    repo_builder: RepoBuilder,
):
    repo = await repo_builder({"retention_period": 30})
    # We have the following log entity hierarchy:
    # - A
    #   - AA
    #   - AB
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AA"],
        saved_at=datetime.now() - timedelta(days=40),
    )
    await repo.create_log_with_entity_path(
        superadmin_client,
        ["A", "AB"],
        saved_at=datetime.now() - timedelta(days=40),
    )

    async with open_db_session() as session:
        await LogService.apply_log_retention_period(session)

    await superadmin_client.assert_get_ok(
        f"/repos/{repo.id}/logs/entities",
        expected_json={
            "items": [],
            "pagination": {
                "next_cursor": None,
            },
        },
    )
