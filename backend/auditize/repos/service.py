from bson import ObjectId

from auditize.repos.models import Repo
from auditize.common.mongo import Database


async def create_repo(db: Database, repo: Repo):
    result = await db.repos.insert_one(repo.model_dump(exclude={"id"}))
    return result.inserted_id
