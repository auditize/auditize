from fastapi import APIRouter, FastAPI
from fastapi.exceptions import RequestValidationError

from auditize.apikey.api import router as apikey_api_router
from auditize.app.cors import setup_cors
from auditize.auth.api import router as auth_api_router
from auditize.exceptions import AuditizeException
from auditize.helpers.api.errors import (
    make_response_from_exception,
)
from auditize.i18n import get_request_lang
from auditize.info.api import router as info_api_router
from auditize.log.api import router as log_api_router
from auditize.log_filter.api import router as log_filter_api_router
from auditize.log_i18n_profile.api import router as log_i18n_profile_api_router
from auditize.openapi import customize_openapi
from auditize.repo.api import router as repo_api_router
from auditize.user.api import router as user_api_router


def _exception_handler(request, exc):
    return make_response_from_exception(exc, get_request_lang(request))


def build_app(*, cors_allow_origins: list[str], online_doc: bool):
    if online_doc:
        app = FastAPI()
    else:
        app = FastAPI(openapi_url=None)
    app.add_exception_handler(AuditizeException, _exception_handler)
    app.add_exception_handler(RequestValidationError, _exception_handler)
    customize_openapi(app)
    router = APIRouter()
    router.include_router(auth_api_router)
    router.include_router(log_api_router)
    router.include_router(repo_api_router)
    router.include_router(user_api_router)
    router.include_router(apikey_api_router)
    router.include_router(log_i18n_profile_api_router)
    router.include_router(log_filter_api_router)
    router.include_router(info_api_router)
    app.include_router(router)
    setup_cors(app, cors_allow_origins=cors_allow_origins)
    return app
