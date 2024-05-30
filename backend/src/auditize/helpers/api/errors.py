from typing import TypeVar

from fastapi.exceptions import RequestValidationError
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


class ApiValidationErrorResponse(BaseModel):
    class ValidationErrorDetail(BaseModel):
        field: str
        message: str

        @classmethod
        def from_dict(cls, error: dict[str, any]):
            return cls(field=".".join(map(str, error["loc"][1:])), message=error["msg"])

    message: str
    validation_errors: list[ValidationErrorDetail]

    @classmethod
    def from_exception(cls, exc: RequestValidationError, _):
        return cls(
            message="Bad request",
            validation_errors=list(
                map(cls.ValidationErrorDetail.from_dict, exc.errors())
            ),
        )


_EXCEPTION_RESPONSES = {
    ValidationError: (400, "Bad request", ApiErrorResponse),
    RequestValidationError: (422, "Bad request", ApiValidationErrorResponse),
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
