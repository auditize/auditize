from httpx import AsyncClient, ASGITransport, Response
from icecream import ic

from auditize.main import app


class HttpTestHelper(AsyncClient):
    async def assert_request(
        self,
        method: str, path, *, params=None, json=None, files=None, data=None,
        expected_status_code=200, expected_json=None
    ) -> Response:
        ic(method, path)
        ic(json, files, data)
        resp = await self.request(method, path, params=params, json=json, files=files, data=data)
        ic(resp.text)
        if expected_status_code is not None:
            assert resp.status_code == expected_status_code
        if expected_json is not None:
            assert resp.json() == expected_json
        return resp

    async def assert_post(
        self,
        path, *, json=None, files=None, data=None,
        expected_status_code=200, expected_json=None
    ) -> Response:
        return await self.assert_request(
            "POST", path,
            json=json, files=files, data=data,
            expected_status_code=expected_status_code, expected_json=expected_json
        )

    async def assert_patch(
        self,
        path, *, json=None, files=None, data=None,
        expected_status_code=204, expected_json=None
    ) -> Response:
        return await self.assert_request(
            "PATCH", path,
            json=json, files=files, data=data,
            expected_status_code=expected_status_code, expected_json=expected_json
        )

    async def assert_delete(
        self,
        path, *,
        expected_status_code=204, expected_json=None
    ) -> Response:
        return await self.assert_request(
            "DELETE", path,
            expected_status_code=expected_status_code, expected_json=expected_json
        )

    async def assert_get(
        self,
        path, *, params=None,
        expected_status_code=200, expected_json=None
    ) -> Response:
        return await self.assert_request(
            "GET", path, params=params,
            expected_status_code=expected_status_code, expected_json=expected_json
        )


def create_http_client():
    return HttpTestHelper(transport=ASGITransport(app=app), base_url="http://localhost")
