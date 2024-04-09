from bson import ObjectId

from auditize.repos.models import Repo, RepoUpdate
from auditize.common.mongo import Database
from auditize.common.exceptions import UnknownModelException


async def create_repo(db: Database, repo: Repo):
    result = await db.repos.insert_one(repo.model_dump(exclude={"id"}))
    return result.inserted_id


async def update_repo(db: Database, repo_id: ObjectId | str, update: RepoUpdate):
    result = await db.repos.update_one(
        {"_id": ObjectId(repo_id)},
        {"$set": update.model_dump(exclude_unset=True)}
    )
    if result.matched_count == 0:
        raise UnknownModelException()
