from contextlib import contextmanager


class AuditizeException(Exception):
    pass


class ConfigError(AuditizeException):
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
def enhance_constraint_violation_exception(trans_key):
    try:
        yield
    except ConstraintViolation:
        raise ConstraintViolation((trans_key,))
