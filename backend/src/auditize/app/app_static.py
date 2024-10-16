import os.path as osp

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

from auditize.app.cors import setup_cors

_STATIC_DIR = osp.join(osp.dirname(__file__), osp.pardir, "data", "html")


async def _index_html_redirection(request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        return FileResponse(osp.join(_STATIC_DIR, "index.html"))
    return response


def build_app(*, cors_allow_origins: list[str]):
    app = FastAPI(openapi_url=None)
    app.mount("", StaticFiles(directory=_STATIC_DIR, check_dir=False))
    app.add_middleware(BaseHTTPMiddleware, dispatch=_index_html_redirection)
    setup_cors(app, cors_allow_origins=cors_allow_origins)
    return app
