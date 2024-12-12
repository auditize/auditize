import base64
import binascii
import json

from auditize.exceptions import InvalidPaginationCursor


def load_pagination_cursor(value: str) -> dict:
    try:
        return json.loads(base64.b64decode(value).decode("utf-8"))
    except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
        raise InvalidPaginationCursor(value)


def serialize_pagination_cursor(data: dict) -> str:
    return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
