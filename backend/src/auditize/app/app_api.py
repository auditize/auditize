from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError

from auditize.apikey.api import router as apikey_api_router
from auditize.auth.api import router as auth_api_router
from auditize.database import init_dbm
from auditize.exceptions import AuditizeException
from auditize.helpers.api.errors import (
    make_response_from_exception,
)
from auditize.i18n import get_request_lang
from auditize.log.api import router as log_api_router
from auditize.log_filter.api import router as log_filter_api_router
from auditize.log_i18n_profile.api import router as log_i18n_profile_api_router
from auditize.openapi import customize_openapi
from auditize.repo.api import router as repo_api_router
from auditize.user.api import router as user_api_router


@asynccontextmanager
async def setup_db(_):
    dbm = init_dbm()
    await dbm.setup()
    yield


def exception_handler(request, exc):
    return make_response_from_exception(exc, get_request_lang(request))


app = FastAPI()
app.add_exception_handler(AuditizeException, exception_handler)
app.add_exception_handler(RequestValidationError, exception_handler)
customize_openapi(app)


###
# Router
###

router = APIRouter()
router.include_router(auth_api_router)
router.include_router(log_api_router)
router.include_router(repo_api_router)
router.include_router(user_api_router)
router.include_router(apikey_api_router)
router.include_router(log_i18n_profile_api_router)
router.include_router(log_filter_api_router)

app.include_router(router)
