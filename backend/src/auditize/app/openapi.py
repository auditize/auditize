from fastapi.openapi.utils import get_openapi


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


def _customize_openapi_schema(schema):
    _fix_nullable(schema)
    _fix_422(schema)
    _add_security_scheme(schema)


def customize_openapi(app):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="Auditize",
            version="0.1.0",
            description="Auditize API",
            routes=app.routes,
        )

        _customize_openapi_schema(openapi_schema)

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
