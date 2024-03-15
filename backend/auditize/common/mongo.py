from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection


class _Collection:
    def __init__(self, name):
        self.name = name

    def __get__(self, db: "Database", _) -> AsyncIOMotorCollection:
        return db.client.get_database(db.name).get_collection(self.name)


class Database:
    def __init__(self, name: str, client: AsyncIOMotorClient):
        self.name = name
        self.client = client

    logs = _Collection("logs")
    log_events = _Collection("log_events")
    log_source_keys = _Collection("log_source_keys")
    log_actor_types = _Collection("log_actor_types")
    log_actor_extra_keys = _Collection("log_actor_extra_keys")
    log_resource_types = _Collection("log_resource_types")
    log_resource_extra_keys = _Collection("log_resource_extra_keys")
    log_detail_keys = _Collection("log_detail_keys")
    log_tag_categories = _Collection("log_tag_categories")
    log_nodes = _Collection("log_nodes")


mongo_client = AsyncIOMotorClient()


def get_db() -> Database:
    return Database("auditize", mongo_client)
