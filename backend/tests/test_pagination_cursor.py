import uuid
from datetime import datetime

import pytest

from auditize.helpers.pagination.cursor.service import (
    InvalidPaginationCursor,
    PaginationCursor,
)


def test_pagination_cursor():
    # build initial cursor
    obj_id = uuid.UUID("cc12c9bb-0b33-43cd-a410-e3f9c848a62b")
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
