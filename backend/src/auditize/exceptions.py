from contextlib import contextmanager
from functools import partial


class AuditizeException(Exception):
    pass


class MigrationLocked(Exception):
    pass


class ConfigError(AuditizeException):
    pass


class ConfigNotInitialized(ConfigError):
    pass


class ConfigAlreadyInitialized(ConfigError):
    pass


class NotFoundError(AuditizeException):
    pass


class AuthenticationFailure(AuditizeException):
    pass


class PermissionDenied(AuditizeException):
    pass


class ValidationError(AuditizeException):
    pass


# NB: a custom exception is not really necessary, but it makes tests easier
class InvalidPaginationCursor(ValidationError):
    pass


class ConstraintViolation(AuditizeException):
    pass


class PayloadTooLarge(AuditizeException):
    pass


class InternalError(AuditizeException):
    pass


@contextmanager
def _enhance_exception(exc_class, trans_key):
    try:
        yield
    except exc_class:
        raise exc_class((trans_key,))


enhance_unknown_model_exception = partial(_enhance_exception, NotFoundError)
