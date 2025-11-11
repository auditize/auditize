import asyncio

from auditize.database import get_dbm
from auditize.log.service import complete_reindex, get_reindex_status, reindex_index
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


async def test_reindex(repo: PreparedRepo, superadmin_client: HttpTestHelper):
    await repo.create_log(superadmin_client)
    elastic_client = get_dbm().elastic_client
    task_id = await reindex_index(elastic_client, repo.log_db_name, target_version=5)
    await repo.create_log(superadmin_client)
    for _ in range(10):
        status = await get_reindex_status(elastic_client, task_id)
        if status["completed"]:
            break
        await asyncio.sleep(1)
    else:
        raise Exception("Could not get completed reindex task after 10s")

    await complete_reindex(elastic_client, repo.log_db_name)

    resp = await superadmin_client.assert_get_ok(f"/repos/{repo.id}/logs")

    assert (await repo.get_log_count()) == 2
