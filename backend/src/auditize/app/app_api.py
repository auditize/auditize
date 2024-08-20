from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError

from auditize.apikey.api import router as apikeys_router
from auditize.app.cors import setup_cors
from auditize.auth.api import router as auth_router
from auditize.database import get_dbm
from auditize.exceptions import AuditizeException
from auditize.helpers.api.errors import (
    make_response_from_exception,
)
from auditize.i18n import get_request_lang
from auditize.log.api import router as logs_router
from auditize.log_filter.api import router as log_filters_router
from auditize.log_i18n_profile.api import router as logi18nprofiles_router
from auditize.openapi import customize_openapi
from auditize.repo.api import router as repos_router
from auditize.user.api import router as users_router


@asynccontextmanager
async def setup_db(_):
    dbm = await get_dbm()
    await dbm.setup()
    yield


def exception_handler(request, exc):
    return make_response_from_exception(exc, get_request_lang(request))


app = FastAPI(lifespan=setup_db)
app.add_exception_handler(AuditizeException, exception_handler)
app.add_exception_handler(RequestValidationError, exception_handler)
setup_cors(app)
customize_openapi(app)


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
