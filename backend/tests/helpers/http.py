from http.cookiejar import Cookie

from starlette.requests import Request

from httpx import AsyncClient, ASGITransport, Response
from icecream import ic

from auditize.main import app


class HttpTestHelper(AsyncClient):
    async def assert_request(
        self,
        method: str, path, *, params=None, json=None, files=None, data=None,
        expected_status_code=200, expected_json=None
    ) -> Response:
        ic("REQUEST", id(self), method, path, self.headers, params, json, files, data)
        resp = await self.request(method, path, params=params, json=json, files=files, data=data)
        ic("RESPONSE", id(self), resp.status_code, resp.headers, resp.text)
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
    return HttpTestHelper(transport=ASGITransport(app=app), base_url="https://localhost")


def get_cookie_by_name(resp: Response, name) -> Cookie:
    for cookie in resp.cookies.jar:
        if cookie.name == name:
            return cookie
    raise LookupError(f"Cookie {name} not found")


# Some useful links about ASGI scope and Starlette:
# - https://www.encode.io/articles/asgi-http
# - https://www.encode.io/articles/working-with-http-requests-in-asgi

def make_http_request(*, headers: dict = None) -> Request:
    if headers is None:
        headers = {}

    scope = {
        "type": "http",
        "method": "GET",
        "scheme": "http",
        "server": ("localhost", 8000),
        "path": "/",
        "headers": [
            [key.lower().encode(), value.encode()] for key, value in headers.items()
        ],
    }

    return Request(scope)
