import json
from pathlib import Path

import pytest

from auditize.database.dbm import get_dbm, open_db_session
from auditize.log.index import reindex_index
from helpers.http import HttpTestHelper
from helpers.log import assert_elastic_log_document
from helpers.repo import PreparedRepo


async def create_index(*, version: int, mapping: dict, settings: dict):
    dbm = get_dbm()
    elastic_client = dbm.elastic_client
    index = f"{dbm.name}_index_v{version}"
    await elastic_client.indices.create(
        index=index,
        mappings=mapping,
        settings=settings,
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


@pytest.mark.parametrize("version", [1, 2])
async def test_reindex_from_previous_version(
    superadmin_client: HttpTestHelper, version: int
):
    resource_path = Path(__file__).parent / "data" / "reindex" / f"v{version}"
    elastic_client = get_dbm().elastic_client

    # Create index & insert document
    index = await create_index(
        version=version,
        mapping=json.loads((resource_path / "mapping.json").read_text()),
        settings=json.loads((resource_path / "settings.json").read_text()),
    )
    await elastic_client.index(
        index=index,
        document=json.loads((resource_path / "input_document.json").read_text()),
        refresh=True,
    )

    # Create repo given the previously created index & reindex
    repo = await PreparedRepo.create(None, index)
    async with open_db_session() as session:
        await reindex_index(session, repo.id)

    # Check API response & Elastic document
    expected_api_response = json.loads(
        (resource_path / "expected_api_response.json").read_text()
    )
    expected_document = json.loads(
        (resource_path / "expected_document.json").read_text()
    )
    resp = await superadmin_client.assert_get_ok(
        f"/repos/{repo.id}/logs/{expected_api_response['id']}"
    )
    assert resp.json() == expected_api_response
    await assert_elastic_log_document(
        repo, expected_api_response["id"], expected_document
    )


async def test_reindex_already_up_to_date(repo: PreparedRepo, capsys):
    async with open_db_session() as session:
        await reindex_index(session, repo.id)
        out, _ = capsys.readouterr()
        assert "already at version" in out
