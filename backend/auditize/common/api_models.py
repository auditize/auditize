from datetime import datetime, timezone
import re


_DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def validate_datetime(value):
    """
    Validate datetime string in ISO 8601 format ("YYYY-MM-DDTHH:MM:SS.sssZ" to be specific).
    """
    if isinstance(value, str) and not _DATETIME_PATTERN.match(value):
        raise ValueError(f'invalid datetime format, expected "{_DATETIME_PATTERN.pattern}", got "{value}"')
    return value


def serialize_datetime(dt: datetime, with_milliseconds=False) -> str:
    """
    Serialize a datetime object to a string in ISO 8601 format ("YYYY-MM-DDTHH:MM:SS[.sss]Z" to be specific).

    :param dt: the datetime object to serialize
    :param with_milliseconds: whether to include milliseconds in the output
    """
    # first, make sure we're dealing with an appropriate UTC datetime:
    dt = dt.astimezone(timezone.utc)
    # second, remove timezone info so that isoformat() won't indicate "+00:00":
    dt = dt.replace(tzinfo=None)
    # third, format:
    return dt.isoformat(timespec="milliseconds" if with_milliseconds else "seconds") + "Z"
