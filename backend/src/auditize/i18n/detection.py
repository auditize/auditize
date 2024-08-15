from fastapi import Request

from auditize.i18n.support import DEFAULT_LANG, SUPPORTED_LANGUAGES


def _get_request_lang(request: Request) -> str:
    try:
        return request.query_params["lang"]
    except KeyError:
        pass

    try:
        return request.state.auditize_lang
    except AttributeError:
        pass

    return DEFAULT_LANG


def get_request_lang(request: Request) -> str:
    lang = _get_request_lang(request)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANG
    return lang
