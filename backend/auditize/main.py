from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic
from pymongo.errors import DuplicateKeyError

from auditize.logs.api import router as logs_router
from auditize.repos.api import router as repos_router
from auditize.users.api import router as users_router
from auditize.integrations.api import router as integrations_router
from auditize.common.exceptions import UnknownModelException, AuthenticationFailure
from auditize.common.api import make_404_response, make_409_response, make_401_response
from auditize.common.db import get_dbm

ic.configureOutput(includeContext=True)


@asynccontextmanager
async def setup_db(_):
    # FIXME: avoid initializing the default database in a test context
    dbm = get_dbm()
    await dbm.setup()
    yield


app = FastAPI(lifespan=setup_db)

# Allow CORS for the frontend (FIXME: make this configurable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add exception handlers

@app.exception_handler(UnknownModelException)
def resource_not_found_handler(request, exc):
    return make_404_response()


@app.exception_handler(DuplicateKeyError)
def duplicate_key_handler(request, exc):
    return make_409_response()


@app.exception_handler(AuthenticationFailure)
def authentication_failure(request, exc):
    return make_401_response()


app.include_router(logs_router)
app.include_router(repos_router)
app.include_router(users_router)
app.include_router(integrations_router)
