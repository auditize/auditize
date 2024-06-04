from typing import TypeVar

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from auditize.exceptions import (
    AuthenticationFailure,
    ConstraintViolation,
    PayloadTooLarge,
    PermissionDenied,
    UnknownModelException,
    ValidationError,
)


class ApiErrorResponse(BaseModel):
    message: str = Field(json_schema_extra={"example": "An error occurred"})

    @classmethod
    def from_exception(cls, exc: Exception, default_message: str):
        return cls(message=str(exc) or default_message)


class ApiValidationErrorResponse(BaseModel):
    class ValidationErrorDetail(BaseModel):
        field: str | None = Field()
        message: str

        @classmethod
        def from_dict(cls, error: dict[str, any]):
            if len(error["loc"]) > 1:
                return cls(
                    field=".".join(map(str, error["loc"][1:])), message=error["msg"]
                )
            else:
                return cls(field=None, message=error["msg"])

    message: str
    validation_errors: list[ValidationErrorDetail] = Field()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Invalid request",
                "validation_errors": [
                    {"field": "field1", "message": "Error message 1"},
                    {"field": "field2", "message": "Error message 2"},
                ],
            }
        }
    )

    @classmethod
    def from_exception(cls, exc: Exception, default_message: str):
        if isinstance(exc, RequestValidationError):
            errors = exc.errors()
            if len(errors) == 0:
                # This should never happen
                return cls(message=default_message, validation_errors=[])
            elif len(errors) == 1 and len(errors[0]["loc"]) == 1:
                # Make a special case for single top-level errors affecting the whole request
                return cls(message=errors[0]["msg"], validation_errors=[])
            return cls(
                # Common case
                message="Invalid request",
                validation_errors=list(
                    map(cls.ValidationErrorDetail.from_dict, exc.errors())
                ),
            )
        else:
            return cls(message=str(exc) or default_message, validation_errors=[])


_EXCEPTION_RESPONSES = {
    ValidationError: (400, "Invalid request", ApiValidationErrorResponse),
    RequestValidationError: (400, "Invalid request", ApiValidationErrorResponse),
    AuthenticationFailure: (401, "Unauthorized", ApiErrorResponse),
    PermissionDenied: (403, "Forbidden", ApiErrorResponse),
    UnknownModelException: (404, "Not found", ApiErrorResponse),
    ConstraintViolation: (409, "Resource already exists", ApiErrorResponse),
    PayloadTooLarge: (413, "Payload too large", ApiErrorResponse),
}
_DEFAULT_EXCEPTION_RESPONSE = (500, "Internal server error", ApiErrorResponse)

E = TypeVar("E", bound=Exception)

_STATUS_CODE_TO_RESPONSE = {
    400: (ApiValidationErrorResponse, "Bad request"),
    401: (ApiErrorResponse, "Unauthorized"),
    403: (ApiErrorResponse, "Forbidden"),
    404: (ApiErrorResponse, "Not found"),
    409: (ApiErrorResponse, "Constraint violation"),
    413: (ApiErrorResponse, "Payload too large"),
}


def error_responses(*status_codes: int):
    return {
        status_code: {
            "description": _STATUS_CODE_TO_RESPONSE[status_code][1],
            "model": _STATUS_CODE_TO_RESPONSE[status_code][0],
        }
        for status_code in status_codes
    }


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
