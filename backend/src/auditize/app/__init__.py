from contextlib import asynccontextmanager

from fastapi import FastAPI

from auditize.app.app_api import build_app as build_api_app
from auditize.app.app_static import build_app as build_static_app
from auditize.app.cors import setup_cors
from auditize.config import get_config, init_config
from auditize.database import (
    acquire_migration_lock,
    get_core_db,
    init_core_db,
    migrate_core_db,
    release_migration_lock,
)
from auditize.exceptions import MigrationLocked
from auditize.log.db import migrate_all_log_dbs

__all__ = ("build_app", "build_api_app", "app_factory")


async def _migrate_all_databases():
    core_db = get_core_db()

    try:
        await acquire_migration_lock(core_db)
    except MigrationLocked:
        return

    try:
        await migrate_core_db(core_db)
        await migrate_all_log_dbs()
    finally:
        await release_migration_lock(core_db)


@asynccontextmanager
async def _setup_app(_):
    await migrate_all_log_dbs()
    yield


def build_app():
    # This function is intended to be used in a context where
    # config and core db have already been initialized
    app = FastAPI(lifespan=_setup_app, openapi_url=None)
    config = get_config()
    app.mount(
        "/api",
        build_api_app(
            cors_allow_origins=config.cors_allow_origins, online_doc=config.online_doc
        ),
    )
    app.mount("/", build_static_app(cors_allow_origins=config.cors_allow_origins))
    return app


def app_factory():
    # This function is intended to be used with
    # uvicorn auditize.app:app_factory --factory
    init_config()
    init_core_db()

    return build_app()
