from contextlib import asynccontextmanager

from fastapi import FastAPI

from auditize.app.app_api import build_app as build_api_app
from auditize.app.app_static import build_app as build_static_app
from auditize.app.cors import setup_cors
from auditize.config import get_config, init_config
from auditize.database import init_core_db, migrate_databases

__all__ = ("build_app", "build_api_app", "app_factory")


@asynccontextmanager
async def _setup_app(_):
    init_core_db()
    await migrate_databases()
    yield


def build_app():
    # This function is intended to be used in a context where
    # config and core db have already been initialized
    app = FastAPI(openapi_url=None)
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
    config = init_config()
    app = FastAPI(lifespan=_setup_app, openapi_url=None)
    app.mount(
        "/api",
        build_api_app(
            cors_allow_origins=config.cors_allow_origins, online_doc=config.online_doc
        ),
    )
    app.mount("/", build_static_app(cors_allow_origins=config.cors_allow_origins))
    return app
