import re

from auditize.exceptions import ValidationError

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
