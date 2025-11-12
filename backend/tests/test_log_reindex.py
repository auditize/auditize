import asyncio

from auditize.database import get_dbm
from auditize.log.service import complete_reindex, get_reindex_status, reindex_index
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


async def test_reindex(repo: PreparedRepo, superadmin_client: HttpTestHelper):
    # Create a log before reindex
    await repo.create_log(superadmin_client)

    # Start reindex with a fake target version and get task ID
    elastic_client = get_dbm().elastic_client
    task_id = await reindex_index(elastic_client, repo.log_db_name, target_version=9999)

    # Add another log after reindex starts
    await repo.create_log(superadmin_client)

    # Wait for reindex to complete (max 10s)
    for _ in range(10):
        status = await get_reindex_status(elastic_client, task_id)
        if status["completed"]:
            break
        await asyncio.sleep(1)
    else:
        raise Exception("Could not get completed reindex task after 10s")

    # Finalize reindex
    await complete_reindex(elastic_client, repo.log_db_name)

    # Check that both logs are present
    resp = await superadmin_client.assert_get_ok(f"/repos/{repo.id}/logs")
    assert (await repo.get_log_count()) == 2
