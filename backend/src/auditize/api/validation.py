import re

from auditize.exceptions import ValidationError
from auditize.helpers.datetime import serialize_datetime

IDENTIFIER_PATTERN_STRING = r"^[a-z0-9-]+$"
IDENTIFIER_PATTERN = re.compile(IDENTIFIER_PATTERN_STRING)
FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN_STRING = (
    r"(?:source|details|actor|resource)\.[a-z0-9-]+"
)
FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN = re.compile(
    FULLY_QUALIFIED_CUSTOM_FIELD_NAME_PATTERN_STRING
)


def validate_bool(value: str) -> bool:
    match value:
        case "true":
            return True
        case "false":
            return False
        case _:
            raise ValidationError(
                f"Invalid boolean value: {value!r} (must be 'true' or 'false')"
            )


def validate_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        raise ValidationError(f"Invalid integer value: {value!r} (must be an integer)")


def validate_float(value: str) -> float:
    try:
        return float(value)
    except ValueError:
        raise ValidationError(f"Invalid float value: {value!r} (must be a float)")


def validate_datetime(value: str) -> str:
    try:
        return serialize_datetime(value)
    except ValueError:
        raise ValidationError(
            f"Invalid datetime value: {value!r} (must be a datetime in ISO 8601 format)"
        )
