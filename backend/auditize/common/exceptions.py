class AuditizeException(Exception):
    pass


class UnknownModelException(AuditizeException):
    pass


class AuthenticationFailure(AuditizeException):
    pass
