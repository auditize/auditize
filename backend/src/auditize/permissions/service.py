from motor.motor_asyncio import AsyncIOMotorCollection


async def remove_repo_from_permissions(
    collection: AsyncIOMotorCollection, repo_id: str
):
    await collection.update_many(
        {"permissions.logs.repos.repo_id": repo_id},
        {"$pull": {"permissions.logs.repos": {"repo_id": repo_id}}},
    )
