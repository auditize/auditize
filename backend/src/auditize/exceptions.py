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
