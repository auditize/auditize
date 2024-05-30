from typing import TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auditize.exceptions import (
    AuthenticationFailure,
    ConstraintViolation,
    PayloadTooLarge,
    PermissionDenied,
    UnknownModelException,
    ValidationError,
)


class ApiErrorResponse(BaseModel):
    message: str

    @classmethod
    def from_exception(cls, exc: Exception, default_message: str):
        return cls(message=str(exc) or default_message)


_EXCEPTION_RESPONSES = {
    ValidationError: (400, "Bad request", ApiErrorResponse),
    AuthenticationFailure: (401, "Unauthorized", ApiErrorResponse),
    PermissionDenied: (403, "Forbidden", ApiErrorResponse),
    UnknownModelException: (404, "Not found", ApiErrorResponse),
    ConstraintViolation: (409, "Resource already exists", ApiErrorResponse),
    PayloadTooLarge: (413, "Payload too large", ApiErrorResponse),
}
_DEFAULT_EXCEPTION_RESPONSE = (500, "Internal server error", ApiErrorResponse)


class NotFoundResponse(BaseModel):
    detail: str = "Not found"


COMMON_RESPONSES = {404: {"description": "Not found", "model": NotFoundResponse}}

E = TypeVar("E", bound=Exception)


def make_response_from_exception(exc: E):
    if exc.__class__ not in _EXCEPTION_RESPONSES:
        status_code = 500
        error = ApiErrorResponse(message="Internal server error")
    else:
        status_code, default_error_message, error_response_class = _EXCEPTION_RESPONSES[
            exc.__class__
        ]
        error = error_response_class.from_exception(exc, default_error_message)

    return JSONResponse(status_code=status_code, content=error.model_dump())
