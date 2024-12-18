import callee

from .http import HttpTestHelper


async def do_test_page_pagination_common_scenarios(
    client: HttpTestHelper, path: str, items: list
):
    """
    This function assumes that for the given path (with possible query string), the total number of items is 5.
    """
    # first test, without pagination parameters
    await client.assert_get(
        path,
        expected_json={
            "items": items,
            "pagination": {"page": 1, "page_size": 10, "total": 5, "total_pages": 1},
        },
    )

    # second test, with pagination parameters
    await client.assert_get(
        path,
        params={"page": 2, "page_size": 2},
        expected_json={
            "items": items[2:4],
            "pagination": {"page": 2, "page_size": 2, "total": 5, "total_pages": 3},
        },
    )


async def do_test_cursor_pagination_common_scenarios(
    client: HttpTestHelper, path: str, *, params: dict = {}, items: list
):
    """
    This function assumes that for the given path (with possible query string), the total number of items is 5.
    """
    # first test, without pagination parameters
    await client.assert_get(
        path,
        params=params,
        expected_json={
            "items": items,
            "pagination": {"next_cursor": None},
        },
    )

    # second test, get items in two different pages
    resp = await client.assert_get(
        path,
        params={**params, "limit": 3},
        expected_json={
            "items": items[:3],
            "pagination": {"next_cursor": callee.IsA(str)},
        },
    )
    await client.assert_get(
        path,
        params={
            **params,
            "cursor": resp.json()["pagination"]["next_cursor"],
            "limit": 3,
        },
        expected_json={
            "items": items[3:],
            "pagination": {"next_cursor": None},
        },
    )


async def do_test_page_pagination_empty_data(client: HttpTestHelper, path: str):
    await client.assert_get(
        path,
        expected_json={
            "items": [],
            "pagination": {"page": 1, "page_size": 10, "total": 0, "total_pages": 0},
        },
    )


async def do_test_cursor_pagination_empty_data(client: HttpTestHelper, path: str):
    await client.assert_get(
        path,
        expected_json={
            "items": [],
            "pagination": {"next_cursor": None},
        },
    )
