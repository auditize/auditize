import base64
import binascii
import json
import uuid
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorCollection

from auditize.helpers.datetime import serialize_datetime


# NB: a custom exception is not really necessary, but it makes tests easier
class InvalidPaginationCursor(ValueError):
    pass


class PaginationCursor:
    """
    This class assumes a pagination sorted by date and _id
    """

    def __init__(self, date: datetime, id: uuid.UUID):
        self.date = date
        self.id = id

    @classmethod
    def load(cls, value: str) -> "PaginationCursor":
        try:
            decoded = json.loads(base64.b64decode(value).decode("utf-8"))
        except (binascii.Error, UnicodeDecodeError, json.JSONDecodeError):
            raise InvalidPaginationCursor(value)

        try:
            return cls(
                datetime.fromisoformat(decoded["date"]), uuid.UUID(decoded["id"])
            )
        except (KeyError, ValueError):
            raise InvalidPaginationCursor(value)

    def serialize(self) -> str:
        data = {
            "date": serialize_datetime(self.date, with_milliseconds=True),
            "id": str(self.id),
        }
        return base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")


async def find_paginated_by_cursor(
    collection: AsyncIOMotorCollection,
    *,
    id_field,
    date_field,
    filter=None,
    projection=None,
    limit: int = 10,
    pagination_cursor: str = None,
) -> tuple[list, str | None]:
    if filter is None:
        filter = {}

    if pagination_cursor:
        cursor = PaginationCursor.load(pagination_cursor)
        filter = {  # noqa
            **filter,
            "$or": [
                {"saved_at": {"$lt": cursor.date}},
                {
                    "$and": [
                        {"saved_at": {"$eq": cursor.date}},
                        {"_id": {"$lt": cursor.id}},
                    ]
                },
            ],
        }

    results = await collection.find(
        filter, projection, sort=[(date_field, -1), (id_field, -1)], limit=limit + 1
    ).to_list(None)

    # we previously fetched one extra log to check if there are more logs to fetch
    if len(results) == limit + 1:
        # there is still more logs to fetch, so we need to return a next_cursor based on the last log WITHIN the
        # limit range
        next_cursor_obj = PaginationCursor(
            results[-2][date_field], results[-2][id_field]
        )
        next_cursor = next_cursor_obj.serialize()
        # remove the extra log
        results.pop(-1)
    else:
        next_cursor = None

    return results, next_cursor
