import asyncio

from auditize.database.dbm import open_db_session
from auditize.log.index import complete_reindex, get_reindex_status, reindex_index
from auditize.repo.service import get_repo
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


async def test_reindex(repo: PreparedRepo, superadmin_client: HttpTestHelper):
    async with open_db_session() as session:
        # Create a log before reindex
        await repo.create_log(superadmin_client)

        # Start reindex with a fake target version and get task ID
        actual_repo = await get_repo(session, repo.id)
        task_id = await reindex_index(actual_repo, target_version=9999)

        # Add another log after reindex starts
        await repo.create_log(superadmin_client)

        # Wait for reindex to complete (max 10s)
        for _ in range(10):
            status = await get_reindex_status(task_id)
            if status["completed"]:
                break
            await asyncio.sleep(1)
        else:
            raise Exception("Could not get completed reindex task after 10s")

        # Finalize reindex
        await complete_reindex(actual_repo)

        # Check that both logs are present
        resp = await superadmin_client.assert_get_ok(f"/repos/{repo.id}/logs")
        assert (await repo.get_log_count()) == 2
