from datetime import datetime, timezone


def serialize_datetime(dt: datetime | str) -> str:
    """
    Serialize a datetime object (or str in ISO 8601 format)
    to a string in ISO 8601 format ("YYYY-MM-DDTHH:MM:SS.sssZ" to be specific).
    """
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    # make sure we're dealing with an appropriate UTC datetime:
    dt = dt.astimezone(timezone.utc)
    # remove timezone info so that isoformat() won't indicate "+00:00":
    dt = dt.replace(tzinfo=None)
    # format:
    return dt.isoformat(timespec="milliseconds") + "Z"


# NB: this function doesn't do much and is mostly here to ease monkey-patching when we want
# to test time-related features (e.g. token expiration)
def now() -> datetime:
    return datetime.now(timezone.utc)
