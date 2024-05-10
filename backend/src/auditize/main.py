from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic

from auditize.apikeys.api import router as apikeys_router
from auditize.auth.api import router as auth_router
from auditize.config import get_config
from auditize.database import get_dbm
from auditize.exceptions import AuditizeException
from auditize.helpers.api.errors import (
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


def setup_cors():
    config = get_config()
    if not config.is_cors_enabled():
        return

    # FIXME: CORS is currently untested as the app is loaded once the module is imported
    # putting this under tests would require to to build the app through a function.
    # Please note that is directly supported by uvicorn through the --factory option.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allow_origins,
        allow_credentials=config.cors_allow_credentials,
        allow_methods=config.cors_allow_methods,
        allow_headers=config.cors_allow_headers,
    )


app = FastAPI(lifespan=setup_db)

###
# Setup CORS according to the configuration
###

setup_cors()


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
