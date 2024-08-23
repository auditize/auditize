from fastapi import Request

from auditize.i18n.lang import Lang


def _get_request_lang(request: Request) -> str | None:
    try:
        return request.query_params["lang"]
    except KeyError:
        pass

    try:
        return request.state.auditize_lang
    except AttributeError:
        pass

    return None


def get_request_lang(request: Request) -> Lang:
    try:
        return Lang(_get_request_lang(request))
    except ValueError:
        return Lang.EN
