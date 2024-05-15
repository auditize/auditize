import re
from datetime import datetime, timezone

DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def validate_datetime(value: str | datetime | None):
    # NB: consider empty string as None
    if not value:
        return None

    # please note that the function also accepts datetime as value because FastAPI seems to
    # call validators twice (the first time with a str, the second time with this str converted into a datetime)
    # when the validator is used with BeforeValidator
    if isinstance(value, datetime):
        return value

    if not DATETIME_PATTERN.match(value):
        raise ValueError(
            f'invalid datetime format, expected "{DATETIME_PATTERN.pattern}", got "{value}"'
        )
    return value


def serialize_datetime(dt: datetime, with_milliseconds=False) -> str:
    """
    Serialize a datetime object to a string in ISO 8601 format ("YYYY-MM-DDTHH:MM:SS[.sss]Z" to be specific).
    """
    # first, make sure we're dealing with an appropriate UTC datetime:
    dt = dt.astimezone(timezone.utc)
    # second, remove timezone info so that isoformat() won't indicate "+00:00":
    dt = dt.replace(tzinfo=None)
    # third, format:
    return (
        dt.isoformat(timespec="milliseconds" if with_milliseconds else "seconds") + "Z"
    )


# NB: this function doesn't do much and is mostly here to ease monkey-patching when we want
# to test time-related features (e.g. token expiration)
def now() -> datetime:
    return datetime.now(timezone.utc)
