from contextlib import asynccontextmanager

from fastapi import FastAPI

from auditize.app.app_api import app as api_app
from auditize.app.app_static import app as static_app
from auditize.app.cors import setup_cors
from auditize.database import get_dbm

__all__ = "app", "api_app"


@asynccontextmanager
async def setup_app(_):
    dbm = await get_dbm()
    await dbm.setup()
    await setup_cors(api_app)
    await setup_cors(static_app)
    yield


app = FastAPI(lifespan=setup_app)
app.mount("/api", api_app)
app.mount("/", static_app)
