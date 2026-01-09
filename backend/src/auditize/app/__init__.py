from fastapi import FastAPI
from fastmcp import FastMCP

from auditize.app.app_api import build_app as build_api_app
from auditize.app.app_static import build_app as build_static_app
from auditize.config import get_config, init_config
from auditize.database import init_dbm
from auditize.mcp import mcp

__all__ = ("build_app", "build_api_app", "app_factory")


def build_app():
    # This function is intended to be used in a context where
    # config and core db have already been initialized
    config = get_config()
    api_app = build_api_app(
        cors_allow_origins=config.cors_allow_origins, online_doc=config.online_doc
    )
    mcp_app = mcp.http_app(path="/mcp", transport="streamable-http")
    static_app = build_static_app(cors_allow_origins=config.cors_allow_origins)
    app = FastAPI(openapi_url=None, lifespan=mcp_app.lifespan)
    app.mount("/mcp", mcp_app)
    app.mount("/api", api_app)
    app.mount("/", static_app)
    return app


def app_factory():
    # This function is intended to be used with
    # uvicorn auditize.app:app_factory --factory
    init_config()
    init_dbm()

    return build_app()
