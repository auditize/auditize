from auditize.database.dbm import open_db_session
from auditize.log.index import reindex_index
from helpers.http import HttpTestHelper
from helpers.repo import PreparedRepo


async def test_reindex(repo: PreparedRepo, superadmin_client: HttpTestHelper):
    async with open_db_session() as session:
        # Create a log before reindex
        log_1 = await repo.create_log(superadmin_client)

        # Start reindex with a fake target version and get task ID
        await reindex_index(session, repo.id, target_version=9999)

        # Add another log after reindex starts
        log_2 = await repo.create_log(superadmin_client)

        # Check that both logs are present
        resp = await superadmin_client.assert_get_ok(f"/repos/{repo.id}/logs")
        assert {log["id"] for log in resp.json()["items"]} == {log_1.id, log_2.id}
        assert (await repo.get_log(log_1.id)) is not None
        assert (await repo.get_log(log_2.id)) is not None
