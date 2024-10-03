from contextlib import contextmanager
from functools import partial


class AuditizeException(Exception):
    pass


class ConfigError(AuditizeException):
    pass


class ConfigNotInitialized(ConfigError):
    pass


class ConfigAlreadyInitialized(ConfigError):
    pass


class UnknownModelException(AuditizeException):
    pass


class AuthenticationFailure(AuditizeException):
    pass


class PermissionDenied(AuditizeException):
    pass


class ValidationError(AuditizeException):
    pass


class ConstraintViolation(AuditizeException):
    pass


class PayloadTooLarge(AuditizeException):
    pass


@contextmanager
def _enhance_exception(exc_class, trans_key):
    try:
        yield
    except exc_class:
        raise exc_class((trans_key,))


enhance_constraint_violation_exception = partial(
    _enhance_exception, ConstraintViolation
)
enhance_unknown_model_exception = partial(_enhance_exception, UnknownModelException)
