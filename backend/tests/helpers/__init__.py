from .http import HttpTestHelper


async def do_test_page_pagination_common_scenarios(client: HttpTestHelper, path: str, data: list):
    """
    This function assumes that for the given path (with possible query string), the total number of items is 5.
    """
    # first test, without pagination parameters
    await client.assert_get(
        path,
        expected_json={
            "data": data,
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 5,
                "total_pages": 1
            }
        }
    )

    # second test, with pagination parameters
    await client.assert_get(
        path,
        params={"page": 2, "page_size": 2},
        expected_json={
            "data": data[2:4],
            "pagination": {
                "page": 2,
                "page_size": 2,
                "total": 5,
                "total_pages": 3
            }
        }
    )


async def do_test_page_pagination_empty_data(client: HttpTestHelper, path: str):
    await client.assert_get(
        path,
        expected_json={
            "data": [],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 0,
                "total_pages": 0
            }
        }
    )
