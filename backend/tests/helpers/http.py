from functools import partialmethod
from http.cookiejar import Cookie

from httpx import ASGITransport, AsyncClient, Response
from icecream import ic
from starlette.requests import Request

from auditize.app import app


class HttpTestHelper(AsyncClient):
    async def assert_request(
        self,
        method: str,
        path,
        *,
        params=None,
        headers=None,
        json=None,
        files=None,
        data=None,
        expected_status_code=200,
        expected_json=None,
    ) -> Response:
        path = f"/api{path}"
        ic(
            "REQUEST",
            id(self),
            method,
            path,
            {**self.headers, **(headers or {})},
            params,
            json,
            files,
            data,
        )
        resp = await self.request(
            method,
            path,
            headers=headers,
            params=params,
            json=json,
            files=files,
            data=data,
        )
        ic(
            "RESPONSE",
            id(self),
            resp.elapsed,
            resp.status_code,
            resp.headers,
            resp.text,
        )
        if expected_status_code is not None:
            assert resp.status_code == expected_status_code
        if expected_json is not None:
            assert resp.json() == expected_json
        return resp

    async def assert_post(
        self,
        path,
        *,
        json=None,
        files=None,
        data=None,
        expected_status_code=200,
        expected_json=None,
    ) -> Response:
        return await self.assert_request(
            "POST",
            path,
            json=json,
            files=files,
            data=data,
            expected_status_code=expected_status_code,
            expected_json=expected_json,
        )

    assert_post_ok = partialmethod(assert_post, expected_status_code=200)
    assert_post_created = partialmethod(assert_post, expected_status_code=201)
    assert_post_no_content = partialmethod(assert_post, expected_status_code=204)
    assert_post_bad_request = partialmethod(assert_post, expected_status_code=400)
    assert_post_unauthorized = partialmethod(assert_post, expected_status_code=401)
    assert_post_forbidden = partialmethod(assert_post, expected_status_code=403)
    assert_post_not_found = partialmethod(assert_post, expected_status_code=404)
    assert_post_constraint_violation = partialmethod(
        assert_post, expected_status_code=409
    )

    async def assert_patch(
        self,
        path,
        *,
        json=None,
        files=None,
        data=None,
        expected_status_code=204,
        expected_json=None,
    ) -> Response:
        return await self.assert_request(
            "PATCH",
            path,
            json=json,
            files=files,
            data=data,
            expected_status_code=expected_status_code,
            expected_json=expected_json,
        )

    assert_patch_ok = partialmethod(assert_patch, expected_status_code=200)
    assert_patch_no_content = partialmethod(assert_patch, expected_status_code=204)
    assert_patch_bad_request = partialmethod(assert_patch, expected_status_code=400)
    assert_patch_unauthorized = partialmethod(assert_patch, expected_status_code=401)
    assert_patch_forbidden = partialmethod(assert_patch, expected_status_code=403)
    assert_patch_not_found = partialmethod(assert_patch, expected_status_code=404)
    assert_patch_constraint_violation = partialmethod(
        assert_patch, expected_status_code=409
    )

    async def assert_delete(
        self, path, *, expected_status_code=204, expected_json=None
    ) -> Response:
        return await self.assert_request(
            "DELETE",
            path,
            expected_status_code=expected_status_code,
            expected_json=expected_json,
        )

    assert_delete_no_content = partialmethod(assert_delete, expected_status_code=204)
    assert_delete_unauthorized = partialmethod(assert_delete, expected_status_code=401)
    assert_delete_forbidden = partialmethod(assert_delete, expected_status_code=403)
    assert_delete_not_found = partialmethod(assert_delete, expected_status_code=404)
    assert_delete_constraint_violation = partialmethod(
        assert_delete, expected_status_code=409
    )

    async def assert_get(
        self,
        path,
        *,
        params=None,
        headers=None,
        expected_status_code=200,
        expected_json=None,
    ) -> Response:
        return await self.assert_request(
            "GET",
            path,
            params=params,
            headers=headers,
            expected_status_code=expected_status_code,
            expected_json=expected_json,
        )

    assert_get_ok = partialmethod(assert_get, expected_status_code=200)
    assert_get_bad_request = partialmethod(assert_get, expected_status_code=400)
    assert_get_unauthorized = partialmethod(assert_get, expected_status_code=401)
    assert_get_forbidden = partialmethod(assert_get, expected_status_code=403)
    assert_get_not_found = partialmethod(assert_get, expected_status_code=404)

    @classmethod
    def spawn(cls) -> "HttpTestHelper":
        return cls(transport=ASGITransport(app=app), base_url="https://localhost")


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
