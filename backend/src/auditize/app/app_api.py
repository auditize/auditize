from fastapi import APIRouter, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError

from auditize.api.exception import (
    ApiErrorResponse,
    make_error_response_from_exception,
    make_error_response_from_model,
)
from auditize.apikey.api import router as apikey_api_router
from auditize.app.cors import setup_cors
from auditize.auth.api import router as auth_api_router
from auditize.exceptions import AuditizeException
from auditize.i18n import get_request_lang
from auditize.info.api import router as info_api_router
from auditize.log.api import router as log_api_router
from auditize.log_filter.api import router as log_filter_api_router
from auditize.log_i18n_profile.api import router as log_i18n_profile_api_router
from auditize.logger import get_logger
from auditize.openapi import customize_openapi
from auditize.repo.api import router as repo_api_router
from auditize.user.api import router as user_api_router

logger = get_logger(__name__)


def _exception_handler(request, exc):
    return make_error_response_from_exception(exc, get_request_lang(request))


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

    @app.middleware("http")
    async def exception_handler(request: Request, call_next):
        # The add_exception_handler() method is not enough to handle the base Exception,
        # we need to handle it using a middleware.
        try:
            return await call_next(request)
        except Exception:
            logger.exception("An unexpected error occurred")
            return make_error_response_from_model(
                ApiErrorResponse.build(
                    "Internal server error (see logs for more details)"
                ),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return app
