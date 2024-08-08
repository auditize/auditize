from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError

from auditize.apikey.api import router as apikeys_router
from auditize.app.cors import setup_cors
from auditize.app.openapi import customize_openapi
from auditize.auth.api import router as auth_router
from auditize.database import get_dbm
from auditize.exceptions import AuditizeException
from auditize.helpers.api.errors import (
    make_response_from_exception,
)
from auditize.log_filter.api import router as log_filters_router
from auditize.log_i18n_profile.api import router as logi18nprofiles_router
from auditize.logs.api import router as logs_router
from auditize.repo.api import router as repos_router
from auditize.user.api import router as users_router


@asynccontextmanager
async def setup_db(_):
    dbm = get_dbm()
    await dbm.setup()
    yield


app = FastAPI(lifespan=setup_db)
setup_cors(app)
customize_openapi(app)


###
# Exception handlers
###


@app.exception_handler(AuditizeException)
def exception_handler(_, exc):
    return make_response_from_exception(exc)


@app.exception_handler(RequestValidationError)
def request_validation_error_handler(_, exc):
    return make_response_from_exception(exc)


###
# Router
###

router = APIRouter()
router.include_router(auth_router)
router.include_router(logs_router)
router.include_router(repos_router)
router.include_router(users_router)
router.include_router(apikeys_router)
router.include_router(logi18nprofiles_router)
router.include_router(log_filters_router)

app.include_router(router)
