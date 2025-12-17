from datetime import datetime, timezone

import callee

DATETIME_FORMAT = callee.Regex(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z")


def strip_dict_keys(d: dict, *keys):
    return {key: val for key, val in d.items() if key not in keys}


def serialize_datetime(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc)
    return dt.isoformat(timespec="milliseconds")
