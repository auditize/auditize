from datetime import datetime

import pytest
from bson import ObjectId

from auditize.common.pagination.cursor.service import (
    InvalidPaginationCursor,
    PaginationCursor,
)


def test_pagination_cursor():
    # build initial cursor
    obj_id = ObjectId("60f3b3b3b3b3b3b3b3b3b3b3")
    date = datetime.fromisoformat("2021-07-19T00:00:00Z")
    cursor = PaginationCursor(id=obj_id, date=date)

    # test cursor serialization
    serialized = cursor.serialize()
    assert type(serialized) is str

    # test cursor deserialization
    new_cursor = PaginationCursor.load(serialized)
    assert new_cursor.id == obj_id
    assert new_cursor.date == date


def test_pagination_cursor_invalid_string():
    with pytest.raises(InvalidPaginationCursor):
        PaginationCursor.load("invalid_cursor_string")
