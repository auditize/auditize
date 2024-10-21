from fastapi.openapi.utils import get_openapi
from fastapi.routing import APIRoute

from auditize.version import __version__

_TAGS = [
    {
        "name": "auth",
        "description": "Authentication",
    },
    {
        "name": "user",
        "description": "User management",
    },
    {
        "name": "apikey",
        "description": "API key management",
    },
    {
        "name": "repo",
        "description": "Repository management",
    },
    {
        "name": "log-i18n-profile",
        "description": "Log i18n profile management",
    },
    {
        "name": "log-filter",
        "description": "Log filter management",
    },
    {
        "name": "log",
        "description": "Log API",
    },
    {
        "name": "info",
        "description": "Information API",
    },
    {
        "name": "internal",
        "description": "Internal endpoints (for internal use only)",
    },
]


def _iter_property_fields(schema):
    for component in schema["components"]["schemas"]:
        properties = schema["components"]["schemas"][component].get("properties", {})
        yield from properties.values()


def _iter_parameter_fields(schema):
    for path in schema["paths"]:
        for method in schema["paths"][path]:
            for parameter in schema["paths"][path][method].get("parameters", []):
                yield parameter["schema"]


def _fix_nullable(schema):
    # workaround https://github.com/pydantic/pydantic/issues/7161

    for field in _iter_parameter_fields(schema):
        if (
            "anyOf" in field
            and len(field["anyOf"]) == 2
            and field["anyOf"][1]["type"] == "null"
        ):
            field.update(field["anyOf"][0])
            del field["anyOf"]

    for field in _iter_property_fields(schema):
        if (
            "anyOf" in field
            and len(field["anyOf"]) == 2
            and field["anyOf"][1]["type"] == "null"
        ):
            field.update(field["anyOf"][0])
            del field["anyOf"]
            field["nullable"] = True


def _fix_422(schema):
    # FastAPI enforce 422 responses even if we don't use them
    # (see https://github.com/tiangolo/fastapi/discussions/6695)
    for path in schema["paths"]:
        for method in schema["paths"][path]:
            responses = schema["paths"][path][method].get("responses")
            if responses and "422" in responses:
                del responses["422"]


def _remove_title(schema):
    for field in _iter_property_fields(schema):
        field.pop("title", None)
    for field in _iter_parameter_fields(schema):
        field.pop("title", None)


def _add_security_scheme(schema):
    schema["components"]["securitySchemes"] = {
        "apikeyAuth": {
            "type": "http",
            "scheme": "bearer",
            "description": "The API client must be authenticated through an API key. API keys can be obtained through "
            "the Auditize user interface. "
            "An API key looks like `aak-ewTddehtMoRjBYtbKzaLy8jqn0hZmh78_iy5Ohg_x4Y` "
            "(API keys are always prefixed with `aak-`)",
        }
    }
    schema["security"] = [{"apikeyAuth": []}]


def _filter_out_internal_routes(routes):
    for route in routes:
        if isinstance(route, APIRoute) and "internal" not in route.tags:
            yield route


def _filter_out_empty_tags(tags: list[dict], routes):
    for tag in tags:
        if any(
            tag["name"] in route.tags for route in routes if isinstance(route, APIRoute)
        ):
            yield tag


def _add_slash_api_prefix(schema):
    for path, content in list(schema["paths"].items()):
        schema["paths"]["/api" + path] = content
        del schema["paths"][path]


def get_customized_openapi_schema(app, include_internal_routes=True):
    routes = (
        app.routes
        if include_internal_routes
        else list(_filter_out_internal_routes(app.routes))
    )
    schema = get_openapi(
        title="Auditize",
        version=__version__,
        description="Auditize API",
        routes=routes,
        tags=list(_filter_out_empty_tags(_TAGS, routes)),
    )

    _fix_nullable(schema)
    _fix_422(schema)
    _remove_title(schema)
    _add_security_scheme(schema)
    _add_slash_api_prefix(schema)

    return schema


def customize_openapi(app):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        app.openapi_schema = get_customized_openapi_schema(app)
        return app.openapi_schema

    app.openapi = custom_openapi
