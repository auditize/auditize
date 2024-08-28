from contextlib import asynccontextmanager

from fastapi import FastAPI

from auditize.app.app_api import build_app as build_api_app
from auditize.app.app_static import build_app as build_static_app
from auditize.app.cors import setup_cors
from auditize.config import init_config
from auditize.database import init_dbm

__all__ = ("build_app", "build_api_app")


@asynccontextmanager
async def _setup_app(_):
    dbm = init_dbm()
    await dbm.setup()
    yield


def build_app():
    # This function is intended to be used in a context where
    # config and dbm have already been initialized
    app = FastAPI()
    app.mount("/api", build_api_app())
    app.mount("/", build_static_app())
    return app


def app_factory():
    # This function is intended to be used with
    # uvicorn auditize.app:app_factory --factory
    init_config()
    app = FastAPI(lifespan=_setup_app)
    app.mount("/api", build_api_app())
    app.mount("/", build_static_app())
    return app
