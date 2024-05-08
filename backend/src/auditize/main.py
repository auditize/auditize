from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic
from pymongo.errors import DuplicateKeyError

from auditize.apikeys.api import router as apikeys_router
from auditize.auth.api import router as auth_router
from auditize.common.api import (
    make_400_response,
    make_401_response,
    make_403_response,
    make_404_response,
    make_409_response,
)
from auditize.database import get_dbm
from auditize.exceptions import (
    AuthenticationFailure,
    ConstraintViolation,
    PermissionDenied,
    UnknownModelException,
    ValidationError,
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


@app.exception_handler(ConstraintViolation)
def duplicate_key_handler(request, exc):
    return make_409_response()


@app.exception_handler(AuthenticationFailure)
def authentication_failure(request, exc):
    return make_401_response()


@app.exception_handler(PermissionDenied)
def permission_denied_handler(request, exc):
    return make_403_response()


@app.exception_handler(ValidationError)
def validation_error_handler(request, exc):
    return make_400_response()


app.include_router(auth_router)
app.include_router(logs_router)
app.include_router(repos_router)
app.include_router(users_router)
app.include_router(apikeys_router)
