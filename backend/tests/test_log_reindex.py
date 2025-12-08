from auditize.database.dbm import get_dbm, open_db_session
from auditize.log.index import reindex_index
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


async def create_index_v1():
    dbm = get_dbm()
    elastic_client = dbm.elastic_client
    index = f"{dbm.name}_index"
    await elastic_client.indices.create(
        index=index,
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
        aliases={
            f"{index}_read": {"is_write_index": False},
            f"{index}_write": {"is_write_index": True},
        },
    )
    return index


async def test_reindex(repo: PreparedRepo, superadmin_client: HttpTestHelper):
    async with open_db_session() as session:
        # Create a log before reindex
        log_1 = await repo.create_log(superadmin_client)

        # Start reindex with a fake target version and get task ID
        # (basically, we reindex from the current version to the current version)
        await reindex_index(session, repo.id, target_version=9999)

        # Add another log after reindex starts
        log_2 = await repo.create_log(superadmin_client)

        # Check that both logs are present
        resp = await superadmin_client.assert_get_ok(f"/repos/{repo.id}/logs")
        assert {log["id"] for log in resp.json()["items"]} == {log_1.id, log_2.id}
        assert (await repo.get_log(log_1.id)) is not None
        assert (await repo.get_log(log_2.id)) is not None


async def test_reindex_from_v1(superadmin_client: HttpTestHelper):
    elastic_client = get_dbm().elastic_client
    index = await create_index_v1()
    log_id = "550e8400-e29b-41d4-a716-446655440000"
    await elastic_client.index(
        index=index,
        document={
            "log_id": log_id,
            "saved_at": "2024-01-15T10:30:00.000Z",
            "action": {
                "type": "create-configuration-profile",
                "category": "configuration",
            },
            "source": [
                {"name": "ip", "value": "127.0.0.1"},
                {
                    "name": "user-agent",
                    "value": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                },
            ],
            "actor": {
                "ref": "user:123",
                "type": "user",
                "name": "John Doe",
                "extra": [
                    {"name": "role", "value": "admin"},
                    {"name": "department", "value": "IT"},
                ],
            },
            "resource": {
                "ref": "config-profile:456",
                "type": "config-profile",
                "name": "Production Configuration Profile",
                "extra": [
                    {"name": "environment", "value": "production"},
                    {"name": "version", "value": "1.2.3"},
                ],
            },
            "details": [
                {"name": "field-name-1", "value": "value 1"},
                {"name": "field-name-2", "value": "value 2"},
                {"name": "status", "value": "success"},
            ],
            "tags": [
                {"type": "security", "name": None, "ref": None},
                {"ref": "tag:789", "type": "compliance", "name": "GDPR"},
                {"ref": "tag:101", "type": "audit", "name": "High Priority"},
            ],
            "attachments": [
                {
                    "name": "document.pdf",
                    "type": "document",
                    "mime_type": "application/pdf",
                    "saved_at": "2024-01-15T10:30:05.000Z",
                    "data": "JVBERi0xLjQKJdPr6eEKMSAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMiAwIFIKPj4KZW5kb2JqCjIgMCBvYmoKPDwKL1R5cGUgL1BhZ2VzCi9LaWRzIFszIDAgUl0KL0NvdW50IDEKL01lZGlhQm94IFswIDAgNjEyIDc5Ml0KPj4KZW5kb2JqCjMgMCBvYmoKPDwKL1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovUmVzb3VyY2VzIDQgMCBSCi9Db250ZW50cyA1IDAgUgovTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQo+PgplbmRvYmoKNCAwIG9iago8PAovUHJvY1NldCBbL1BERiAvVGV4dF0KL0ZvbnQgPDwKL0YxIDYgMCBSCj4+Cj4+CmVuZG9iago1IDAgb2JqCjw8Ci9MZW5ndGggNDQKPj4Kc3RyZWFtCkJUCi9GMSAxMiBUZgooVGVzdCBQREYpIFRqCkVUCmVuZHN0cmVhbQplbmRvYmoKNiAwIG9iago8PAovVHlwZSAvRm9udAovU3VidHlwZSAvVHlwZTEKL0Jhc2VGb250IC9IZWx2ZXRpY2EKPj4KZW5kb2JqCnhyZWYKMCA3CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAwOSAwMDAwMCBuIAowMDAwMDAwMDU4IDAwMDAwIG4gCjAwMDAwMDAxMDQgMDAwMDAgbiAKMDAwMDAwMDI3MCAwMDAwMCBuIAowMDAwMDAwMzQxIDAwMDAwIG4gCjAwMDAwMDA0MTcgMDAwMDAgbiAKdHJhaWxlcgo8PAovU2l6ZSA3Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0ODkKJSVFT0Y=",
                },
                {
                    "name": "screenshot.png",
                    "type": "image",
                    "mime_type": "image/png",
                    "saved_at": "2024-01-15T10:30:10.000Z",
                    "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                },
            ],
            "entity_path": [
                {"ref": "customer:1", "name": "Customer 1"},
                {"ref": "entity:1", "name": "Entity 1"},
                {"ref": "subentity:1", "name": "Sub-Entity 1"},
            ],
        },
        refresh=True,
    )
    repo = await PreparedRepo.create(None, index)
    async with open_db_session() as session:
        await reindex_index(session, repo.id)
    resp = await superadmin_client.assert_get_ok(f"/repos/{repo.id}/logs/{log_id}")
    assert resp.json() == {
        "id": log_id,
        "saved_at": "2024-01-15T10:30:00.000Z",
        "action": {
            "type": "create_configuration_profile",
            "category": "configuration",
        },
        "source": [
            {"name": "ip", "value": "127.0.0.1", "type": "string"},
            {
                "name": "user_agent",
                "value": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "type": "string",
            },
        ],
        "actor": {
            "ref": "user:123",
            "type": "user",
            "name": "John Doe",
            "extra": [
                {"name": "role", "value": "admin", "type": "string"},
                {"name": "department", "value": "IT", "type": "string"},
            ],
        },
        "resource": {
            "ref": "config-profile:456",
            "type": "config_profile",
            "name": "Production Configuration Profile",
            "extra": [
                {"name": "environment", "value": "production", "type": "string"},
                {"name": "version", "value": "1.2.3", "type": "string"},
            ],
        },
        "details": [
            {"name": "field_name_1", "value": "value 1", "type": "string"},
            {"name": "field_name_2", "value": "value 2", "type": "string"},
            {"name": "status", "value": "success", "type": "string"},
        ],
        "tags": [
            {"type": "security", "name": None, "ref": None},
            {"ref": "tag:789", "type": "compliance", "name": "GDPR"},
            {"ref": "tag:101", "type": "audit", "name": "High Priority"},
        ],
        "attachments": [
            {
                "name": "document.pdf",
                "type": "document",
                "mime_type": "application/pdf",
                "saved_at": "2024-01-15T10:30:05.000Z",
            },
            {
                "name": "screenshot.png",
                "type": "image",
                "mime_type": "image/png",
                "saved_at": "2024-01-15T10:30:10.000Z",
            },
        ],
        "entity_path": [
            {"ref": "customer:1", "name": "Customer 1"},
            {"ref": "entity:1", "name": "Entity 1"},
            {"ref": "subentity:1", "name": "Sub-Entity 1"},
        ],
    }


async def test_reindex_already_up_to_date(repo: PreparedRepo, capsys):
    async with open_db_session() as session:
        await reindex_index(session, repo.id)
        out, _ = capsys.readouterr()
        assert "already at version" in out
