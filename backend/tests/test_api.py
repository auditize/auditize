###
# Test transversal API concepts
###
from unittest.mock import patch

import callee
import pytest

from helpers.http import HttpTestHelper

pytestmark = pytest.mark.anyio


async def test_bad_json(superadmin_client: HttpTestHelper):
    await superadmin_client.assert_post_bad_request(
        "/repos",
        json="bad json",
        expected_json={
            "message": callee.StartsWith("Input should be a valid"),
            "validation_errors": [],
        },
    )


@pytest.mark.skip("FIXME: Waiting for a proper 500 handling")
async def test_internal_error(superadmin_client: HttpTestHelper):
    with patch("auditize.repos.service.create_repo") as create_repo:
        create_repo.side_effect = Exception("Unexpected error")
        await superadmin_client.assert_post(
            "/repos",
            json={"name": "Repo"},
            expected_status_code=500,
        )


async def test_internal_route_not_found():
    client = HttpTestHelper.spawn()
    await client.assert_post_not_found("/this-route-does-not-exist")
