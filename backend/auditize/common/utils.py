from datetime import datetime, timezone


def serialize_datetime(dt: datetime, with_milliseconds=False) -> str:
    """
    Serialize a datetime object to a string in ISO 8601 format ("YYYY-MM-DDTHH:MM:SS[.sss]Z" to be specific).
    """
    # first, make sure we're dealing with an appropriate UTC datetime:
    dt = dt.astimezone(timezone.utc)
    # second, remove timezone info so that isoformat() won't indicate "+00:00":
    dt = dt.replace(tzinfo=None)
    # third, format:
    return dt.isoformat(timespec="milliseconds" if with_milliseconds else "seconds") + "Z"
