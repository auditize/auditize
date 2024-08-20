import os.path as osp

from fastapi import FastAPI
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

STATIC_DIR = osp.join(osp.dirname(__file__), osp.pardir, "data", "html")

app = FastAPI()
app.mount("", StaticFiles(directory=STATIC_DIR))


@app.middleware("http")
async def index_html_redirection(request, call_next):
    response = await call_next(request)
    if response.status_code == 404:
        return FileResponse(osp.join(STATIC_DIR, "index.html"))
    return response
