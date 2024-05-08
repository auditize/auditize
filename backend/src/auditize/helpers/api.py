from typing import TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pymongo.errors import DuplicateKeyError

from auditize.exceptions import (
    AuthenticationFailure,
    ConstraintViolation,
    PermissionDenied,
    UnknownModelException,
    ValidationError,
)

_EXCEPTION_RESPONSES = {
    ValidationError: (400, "Bad request"),
    AuthenticationFailure: (401, "Unauthorized"),
    PermissionDenied: (403, "Forbidden"),
    UnknownModelException: (404, "Not found"),
    # FIXME: DuplicateKeyError must be re-raised as ConstraintViolation
    DuplicateKeyError: (409, "Resource already exists"),
    ConstraintViolation: (409, "Resource already exists"),
}


class NotFoundResponse(BaseModel):
    detail: str = "Not found"


COMMON_RESPONSES = {404: {"description": "Not found", "model": NotFoundResponse}}

E = TypeVar("E", bound=Exception)


def make_response_from_exception(exc: E):
    status_code, default_error_message = _EXCEPTION_RESPONSES.get(
        exc.__class__, (500, "Internal server error")
    )
    if str(exc) and status_code != 500:
        error_message = str(exc)
    else:
        error_message = default_error_message

    return JSONResponse(status_code=status_code, content={"detail": error_message})
