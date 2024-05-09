import base64
from datetime import datetime

import callee
import pytest

from auditize.database import DatabaseManager
from auditize.logs.models import Log
from auditize.logs.service import (
    consolidate_log_actor,
    consolidate_log_event,
    consolidate_log_node_path,
    consolidate_log_resource,
    consolidate_log_tags,
)
from conftest import ApikeyBuilder
from helpers.http import HttpTestHelper
from helpers.logs import UNKNOWN_OBJECT_ID, PreparedLog
from helpers.pagination import (
    do_test_page_pagination_common_scenarios,
    do_test_page_pagination_empty_data,
)
from helpers.repos import PreparedRepo

pytestmark = pytest.mark.anyio


async def test_log_repo_access_control(
    apikey_builder: ApikeyBuilder, dbm: DatabaseManager
):
    # Test that access control based on repo_id is properly enforced by the API

    repo_1 = await PreparedRepo.create(dbm)
    repo_2 = await PreparedRepo.create(dbm)

    apikey = await apikey_builder(
        {
            "logs": {
                "repos": {
                    repo_1.id: {"write": True},
                }
            }
        }
    )

    async with apikey.client() as client:
        await client.assert_post(
            f"/repos/{repo_1.id}/logs",
            json=PreparedLog.prepare_data(),
            expected_status_code=201,
        )
        await client.assert_post(
            f"/repos/{repo_2.id}/logs",
            json=PreparedLog.prepare_data(),
            expected_status_code=403,
        )


async def test_create_log_minimal_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs",
        json=PreparedLog.prepare_data(),
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)},
    )


async def test_create_log_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_post(
        f"/repos/{repo.id}/logs", json=PreparedLog.prepare_data()
    )


async def test_create_log_all_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    data = PreparedLog.prepare_data(
        {
            "source": {"ip": "1.1.1.1", "user_agent": "Mozilla/5.0"},
            "actor": {
                "type": "user",
                "id": "user:123",
                "name": "User 123",
                "extra": {"role": "admin"},
            },
            "resource": {
                "type": "module",
                "id": "core",
                "name": "Core Module",
                "extra": {"creator": "xyz"},
            },
            "details": {
                "more_details": {"some_key": "some_value"},
                "other_details": {"other_key": "other_value"},
            },
            "tags": [
                {
                    "id": "simple_tag",
                },
                {"id": "rich_tag:1", "category": "rich_tag", "name": "Rich tag"},
            ],
        }
    )

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs",
        json=data,
        expected_status_code=201,
        expected_json={"id": callee.IsA(str)},
    )


async def test_create_log_missing_event_name(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    data = PreparedLog.prepare_data()
    del data["event"]["name"]
    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs", json=data, expected_status_code=422
    )


async def test_create_log_invalid_rich_tag(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    invalid_tags = (
        {"id": "some_tag", "category": "rich_tag"},
        {"id": "some_other_tag", "name": "Rich tag"},
    )

    for invalid_tag in invalid_tags:
        await log_write_client.assert_post(
            f"/repos/{repo.id}/logs",
            json=PreparedLog.prepare_data({"tags": [invalid_tag]}),
            expected_status_code=422,
        )


async def test_add_attachment_text_and_minimal_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_write_client)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
        expected_status_code=204,
    )
    await log.assert_db(
        {
            "attachments": [
                {
                    "name": "test.txt",
                    "type": "text",
                    "mime_type": "text/plain",
                    "data": b"test data",
                }
            ]
        }
    )


async def test_add_attachment_binary_and_all_fields(
    log_write_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_write_client)

    # some random data generated with /dev/urandom:
    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.bin", data)},
        data={
            "type": "binary",
            "name": "test_file.bin",
            "mime_type": "application/octet-stream",
        },
        expected_status_code=204,
    )
    await log.assert_db(
        {
            "attachments": [
                {
                    "name": "test_file.bin",
                    "type": "binary",
                    "mime_type": "application/octet-stream",
                    "data": data,
                }
            ]
        }
    )


async def test_add_attachment_unknown_log(
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{UNKNOWN_OBJECT_ID}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
        expected_status_code=404,
    )


async def test_add_attachment_forbidden(
    log_write_client: HttpTestHelper,
    no_permission_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)
    await no_permission_client.assert_forbidden_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("test.txt", "test data")},
        data={"type": "text"},
    )


async def test_get_log_minimal_fields(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}", expected_json=log.expected_api_response()
    )


async def test_get_log_all_fields(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    data = PreparedLog.prepare_data(
        {
            "source": {"ip": "1.1.1.1", "user_agent": "Mozilla/5.0"},
            "actor": {
                "type": "user",
                "id": "user:123",
                "name": "User 123",
                "extra": {"role": "admin"},
            },
            "resource": {
                "type": "module",
                "id": "core",
                "name": "Core Module",
                "extra": {"creator": "xyz"},
            },
            "details": {
                "more_details": {"some_key": "some_value"},
                "other_details": {"other_key": "other_value"},
            },
            "tags": [
                {
                    "id": "simple_tag",
                },
                {"id": "rich_tag:1", "category": "rich_tag", "name": "Rich tag"},
            ],
        }
    )
    log = await repo.create_log(log_write_client, data)

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}", expected_json=log.expected_api_response()
    )


async def test_get_log_not_found(log_read_client: HttpTestHelper, repo: PreparedRepo):
    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_get_log_unknown_repo(log_read_client: HttpTestHelper):
    await log_read_client.assert_get(
        f"/repos/{UNKNOWN_OBJECT_ID}/logs/{UNKNOWN_OBJECT_ID}", expected_status_code=404
    )


async def test_get_log_forbidden(
    log_write_client: HttpTestHelper,
    no_permission_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)
    await no_permission_client.assert_forbidden_get(f"/repos/{repo.id}/logs/{log.id}")


async def test_get_log_attachment_text_and_minimal_fields(
    log_read_client: HttpTestHelper, log_write_client, repo: PreparedRepo
):
    log = await repo.create_log(log_write_client)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.txt", "test data")},
        data={"type": "text file"},
        expected_status_code=204,
    )

    resp = await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )
    assert resp.headers["Content-Disposition"] == "attachment; filename=file.txt"
    assert resp.headers["Content-Type"] == "text/plain; charset=utf-8"
    assert resp.content == b"test data"


async def test_get_log_attachment_binary_and_all_fields(
    log_read_client: HttpTestHelper,
    log_write_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)

    data_base64 = "srX7jaKuqoXJQm7YocqmFzSwjObc0ycvnMYor28L9Kc="
    data = base64.b64decode(data_base64)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.bin", data)},
        data={"type": "binary", "name": "test_file.bin", "mime_type": "image/jpeg"},
        expected_status_code=204,
    )

    resp = await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )
    assert resp.headers["Content-Disposition"] == "attachment; filename=test_file.bin"
    assert resp.headers["Content-Type"] == "image/jpeg"
    assert resp.content == data


async def test_get_log_attachment_not_found_log_id(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/{UNKNOWN_OBJECT_ID}/attachments/0",
        expected_status_code=404,
    )


async def test_get_log_attachment_not_found_attachment_idx(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)
    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0", expected_status_code=404
    )


async def test_get_log_attachment_forbidden(
    log_write_client: HttpTestHelper,
    no_permission_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log = await repo.create_log(log_write_client)

    await log_write_client.assert_post(
        f"/repos/{repo.id}/logs/{log.id}/attachments",
        files={"file": ("file.txt", "test data")},
        data={"type": "text file"},
        expected_status_code=204,
    )

    await no_permission_client.assert_forbidden_get(
        f"/repos/{repo.id}/logs/{log.id}/attachments/0"
    )


async def test_get_logs(
    log_write_client: HttpTestHelper,
    log_read_client: HttpTestHelper,
    repo: PreparedRepo,
):
    log1 = await repo.create_log(log_write_client)
    log2 = await repo.create_log(log_write_client)

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs",
        expected_json={
            "data": [log2.expected_api_response(), log1.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_unknown_repo(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get(
        f"/repos/{UNKNOWN_OBJECT_ID}/logs", expected_status_code=404
    )


async def test_get_logs_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(f"/repos/{repo.id}/logs")


async def test_get_logs_limit(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    await repo.create_log(log_rw_client)
    log2 = await repo.create_log(log_rw_client)

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs?limit=1",
        expected_json={
            "data": [log2.expected_api_response()],
            "pagination": {"next_cursor": callee.IsA(str)},
        },
    )


async def test_get_logs_limit_and_cursor(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    logs = [await repo.create_log(log_rw_client) for _ in range(10)]

    # first step, get 5 logs and check the next_cursor
    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs?limit=5",
        expected_json={
            "data": [log.expected_api_response() for log in reversed(logs[-5:])],
            "pagination": {"next_cursor": callee.IsA(str)},
        },
    )
    next_cursor = resp.json()["pagination"]["next_cursor"]

    # second step, get the next 5 logs using the next_cursor from the previous response and check next_cursor is None
    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs?limit=5&cursor={next_cursor}",
        expected_json={
            "data": [log.expected_api_response() for log in reversed(logs[:5])],
            "pagination": {"next_cursor": None},
        },
    )


async def _test_get_logs_filter(
    client: HttpTestHelper, repo: PreparedRepo, func, params
):
    await repo.create_log(client)  # a log not be seen in the response
    log2_data = PreparedLog.prepare_data()
    func(log2_data)
    log2 = await repo.create_log(client, log2_data)

    await client.assert_get(
        f"/repos/{repo.id}/logs",
        params=params,
        expected_json={
            "data": [log2.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_event_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["event"]["name"] = "find_me"

    await _test_get_logs_filter(log_rw_client, repo, func, {"event_name": "find_me"})


async def test_get_logs_filter_event_category(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["event"]["category"] = "find_me"

    await _test_get_logs_filter(
        log_rw_client, repo, func, {"event_category": "find_me"}
    )


async def test_get_logs_filter_actor_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["actor"] = {"type": "find_me", "id": "user:123", "name": "User 123"}

    await _test_get_logs_filter(log_rw_client, repo, func, {"actor_type": "find_me"})


async def test_get_logs_filter_actor_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["actor"] = {"type": "user", "id": "user:123", "name": "find_me"}

    # filter on actor_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"actor_name": "FIND"})


async def test_get_logs_filter_resource_type(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["resource"] = {"type": "find_me", "id": "core", "name": "Core Module"}

    await _test_get_logs_filter(log_rw_client, repo, func, {"resource_type": "find_me"})


async def test_get_logs_filter_resource_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["resource"] = {"type": "module", "id": "core", "name": "find_me"}

    # filter on resource_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"resource_name": "FIND"})


async def test_get_logs_filter_tag_category(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "rich_tag:1", "category": "find_me", "name": "Rich tag"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"tag_category": "find_me"})


async def test_get_logs_filter_tag_name(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "rich_tag:1", "category": "rich_tag", "name": "find_me"},
        ]

    # filter on tag_name is substring and case-insensitive
    await _test_get_logs_filter(log_rw_client, repo, func, {"tag_name": "FIND"})


async def test_get_logs_filter_tag_id(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["tags"] = [
            {"id": "simple_tag"},
            {"id": "find_me", "category": "rich_tag", "name": "Rich tag"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"tag_id": "find_me"})


async def test_get_logs_filter_node_id_exact_node(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["node_path"] = [
            {"id": "find_me:1", "name": "Customer 1"},
            {"id": "find_me:2", "name": "Customer 2"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"node_id": "find_me:2"})


async def test_get_logs_filter_node_id_ascendant_node(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    def func(log):
        log["node_path"] = [
            {"id": "find_me:1", "name": "Customer 1"},
            {"id": "find_me:2", "name": "Customer 2"},
        ]

    await _test_get_logs_filter(log_rw_client, repo, func, {"node_id": "find_me:1"})


async def test_get_logs_filter_since(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"since": "2024-01-01T12:00:00Z"},
        expected_json={
            "data": [log2.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_until(log_rw_client: HttpTestHelper, repo: PreparedRepo):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"until": "2024-01-01T12:00:00Z"},
        expected_json={
            "data": [log1.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_until_milliseconds(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2023-12-31T23:59:59.500Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"until": "2023-12-31T23:59:59Z"},
        expected_json={
            "data": [log1.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_filter_between_since_and_until(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log1 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-01T00:00:00Z")
    )
    log2 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-02T00:00:00Z")
    )
    log3 = await repo.create_log(
        log_rw_client, saved_at=datetime.fromisoformat("2024-01-03T00:00:00Z")
    )

    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"since": "2024-01-01T12:00:00Z", "until": "2024-01-02T12:00:00Z"},
    )
    assert resp.json() == {
        "data": [log2.expected_api_response()],
        "pagination": {"next_cursor": None},
    }


async def test_get_logs_filter_multiple_criteria(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log1_data = PreparedLog.prepare_data()
    log1_data["event"]["name"] = "find_me:event_name"
    log1 = await repo.create_log(log_rw_client, log1_data)

    log2_data = PreparedLog.prepare_data()
    log2_data["event"]["category"] = "find_me:event_category"
    log2 = await repo.create_log(log_rw_client, log2_data)

    log3_data = PreparedLog.prepare_data()
    log3_data["event"] = {
        "name": "find_me:event_name",
        "category": "find_me:event_category",
    }
    log3 = await repo.create_log(log_rw_client, log3_data)

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={
            "event_name": "find_me:event_name",
            "event_category": "find_me:event_category",
        },
        expected_json={
            "data": [log3.expected_api_response()],
            "pagination": {"next_cursor": None},
        },
    )


async def test_get_logs_empty_string_filter_params(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)

    resp = await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={
            "event_name": "",
            "event_category": "",
            "actor_type": "",
            "actor_name": "",
            "resource_type": "",
            "resource_name": "",
            "tag_category": "",
            "tag_name": "",
            "tag_id": "",
            "node_id": "",
            "since": "",
            "until": "",
        },
    )
    assert resp.json() == {
        "data": [log.expected_api_response()],
        "pagination": {"next_cursor": None},
    }


async def test_get_logs_filter_no_result(
    log_rw_client: HttpTestHelper, repo: PreparedRepo
):
    log = await repo.create_log(log_rw_client)

    await log_rw_client.assert_get(
        f"/repos/{repo.id}/logs",
        params={"event_name": "not to be found"},
        expected_json={"data": [], "pagination": {"next_cursor": None}},
    )


async def test_get_log_event_categories(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_event(
            repo.db, Log.Event(category=f"category_{i}", name=f"name_{i}")
        )
        await consolidate_log_event(
            repo.db, Log.Event(category=f"category_{i}", name=f"name_{i + 10}")
        )

    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/event-categories",
        [f"category_{i}" for i in range(5)],
    )


async def test_get_log_event_categories_unknown_repo(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await log_read_client.assert_get(
        f"/repos/{UNKNOWN_OBJECT_ID}/logs/event-categories", expected_status_code=404
    )


async def test_get_log_event_categories_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(
        f"/repos/{repo.id}/logs/event-categories"
    )


async def test_get_log_event_categories_empty(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/event-categories"
    )


async def test_get_log_event_names(log_read_client: HttpTestHelper, repo: PreparedRepo):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_event(
            repo.db, Log.Event(category=f"category_{i}", name=f"name_{i}")
        )
        await consolidate_log_event(
            repo.db, Log.Event(category=f"category_{i + 10}", name=f"name_{i}")
        )

    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/events",
        [f"name_{i}" for i in range(5)],
    )

    # test category parameter
    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/events?category=category_2",
        expected_json={
            "data": [f"name_{2}"],
            "pagination": {"page": 1, "page_size": 10, "total": 1, "total_pages": 1},
        },
    )


async def test_get_log_event_names_empty(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/events"
    )


async def test_get_log_event_names_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(f"/repos/{repo.id}/logs/events")


async def test_get_log_actor_types(log_read_client: HttpTestHelper, repo: PreparedRepo):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_actor(
            repo.db, Log.Actor(type=f"type_{i}", id=f"id_{i}", name=f"name_{i}")
        )

    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/actor-types",
        [f"type_{i}" for i in range(5)],
    )


async def test_get_log_actor_types_empty(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/actor-types"
    )


async def test_get_log_actor_types_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(
        f"/repos/{repo.id}/logs/actor-types"
    )


async def test_get_log_resource_types(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    for i in reversed(range(5)):  # insert in reverse order to test sorting
        await consolidate_log_resource(
            repo.db, Log.Resource(type=f"type_{i}", id=f"id_{i}", name=f"name_{i}")
        )

    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/resource-types",
        [f"type_{i}" for i in range(5)],
    )


async def test_get_log_resource_types_empty(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/resource-types"
    )


async def test_get_log_resource_types_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(
        f"/repos/{repo.id}/logs/resource-types"
    )


async def test_get_log_tag_categories(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    for i in reversed(range(5)):
        await consolidate_log_tags(
            repo.db,
            [Log.Tag(id=f"tag_{i}", category=f"category_{i}", name=f"name_{i}")],
        )
    await consolidate_log_tags(
        repo.db, [Log.Tag(id="simple_tag")]
    )  # no category, it must not be returned

    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/tag-categories",
        [f"category_{i}" for i in range(5)],
    )


async def test_get_log_tag_categories_empty(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/tag-categories"
    )


async def test_get_log_tag_categories_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(
        f"/repos/{repo.id}/logs/tag-categories"
    )


async def test_get_log_nodes_without_filters(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    for i in range(4):
        await consolidate_log_node_path(
            repo.db,
            [
                Log.Node(id=f"customer", name=f"Customer"),
                Log.Node(id=f"entity:{i}", name=f"Entity {i}"),
            ],
        )

    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/nodes",
        [
            {
                "id": "customer",
                "name": "Customer",
                "parent_node_id": None,
                "has_children": True,
            }
        ]
        + [
            {
                "id": f"entity:{i}",
                "name": f"Entity {i}",
                "parent_node_id": "customer",
                "has_children": False,
            }
            for i in range(4)
        ],
    )


async def test_get_log_nodes_with_filters(
    log_read_client: HttpTestHelper, repo: PreparedRepo
):
    for i in range(5):
        for j in "a", "b", "c", "d", "e":
            await consolidate_log_node_path(
                repo.db,
                [
                    Log.Node(id=f"customer:{i}", name=f"Customer {i}"),
                    Log.Node(id=f"entity:{i}-{j}", name=f"Entity {j}"),
                ],
            )

    # test top-level nodes
    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/nodes?root=true",
        [
            {
                "id": f"customer:{i}",
                "name": f"Customer {i}",
                "parent_node_id": None,
                "has_children": True,
            }
            for i in range(5)
        ],
    )

    # test non-top-level nodes
    await do_test_page_pagination_common_scenarios(
        log_read_client,
        f"/repos/{repo.id}/logs/nodes?parent_node_id=customer:2",
        [
            {
                "id": f"entity:2-{j}",
                "name": f"Entity {j}",
                "parent_node_id": "customer:2",
                "has_children": False,
            }
            for j in ("a", "b", "c", "d", "e")
        ],
    )


async def test_get_log_nodes_empty(log_read_client: HttpTestHelper, repo: PreparedRepo):
    await do_test_page_pagination_empty_data(
        log_read_client, f"/repos/{repo.id}/logs/nodes"
    )


async def test_get_log_nodes_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(f"/repos/{repo.id}/logs/nodes")


async def test_get_log_node(log_read_client: HttpTestHelper, repo: PreparedRepo):
    await consolidate_log_node_path(
        repo.db,
        [
            Log.Node(id="customer", name="Customer"),
            Log.Node(id="entity", name="Entity"),
        ],
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/nodes/customer",
        expected_json={
            "id": "customer",
            "name": "Customer",
            "parent_node_id": None,
            "has_children": True,
        },
    )

    await log_read_client.assert_get(
        f"/repos/{repo.id}/logs/nodes/entity",
        expected_json={
            "id": "entity",
            "name": "Entity",
            "parent_node_id": "customer",
            "has_children": False,
        },
    )


async def test_get_log_node_forbidden(
    no_permission_client: HttpTestHelper, repo: PreparedRepo
):
    await no_permission_client.assert_forbidden_get(
        f"/repos/{repo.id}/logs/nodes/some_value"
    )
