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


def _customize_openapi_schema(schema):
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
