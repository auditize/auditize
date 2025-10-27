def validate_empty_string_as_none(value: str | None) -> str | None:
    if value == "":
        return None
    return value
