from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic

from auditize.apikeys.api import router as apikeys_router
from auditize.auth.api import router as auth_router
from auditize.database import get_dbm
from auditize.exceptions import AuditizeException
from auditize.helpers.api import (
    make_response_from_exception,
)
from auditize.logs.api import router as logs_router
from auditize.repos.api import router as repos_router
from auditize.users.api import router as users_router

ic.configureOutput(includeContext=True)


@asynccontextmanager
async def setup_db(_):
    # FIXME: avoid initializing the default database in a test context
    dbm = get_dbm()
    await dbm.setup()
    yield


app = FastAPI(lifespan=setup_db)

###
# Allow CORS for the frontend (FIXME: make this configurable)
###


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


###
# Exception handlers
###


@app.exception_handler(AuditizeException)
def resource_not_found_handler(_, exc):
    return make_response_from_exception(exc)


###
# Routers
###

app.include_router(auth_router)
app.include_router(logs_router)
app.include_router(repos_router)
app.include_router(users_router)
app.include_router(apikeys_router)
