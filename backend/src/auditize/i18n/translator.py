import json
import os.path as osp

from auditize.i18n.support import DEFAULT_LANG, SUPPORTED_LANGUAGES


class Translator:
    def __init__(self, translations: dict[str, dict[str, str]]):
        self._translations = translations

    @classmethod
    def load(cls):
        translations_dir = osp.join(osp.dirname(__file__), "translations")
        translations = {}
        for lang in SUPPORTED_LANGUAGES:
            with open(osp.join(translations_dir, f"{lang}.json")) as fh:
                translations[lang] = json.load(fh)
        return cls(translations)

    def __call__(
        self, key: str, values: dict = None, *, lang: str = DEFAULT_LANG
    ) -> str:
        try:
            return self._translations[lang][key].format(**(values or {}))
        except KeyError as excp:
            raise LookupError(
                f"Missing translation or variable for {key!r} in {lang!r}: {excp}"
            )
