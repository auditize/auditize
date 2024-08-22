import json
import os.path as osp

from auditize.i18n.lang import DEFAULT_LANG, Lang


class Translator:
    def __init__(self, translations: dict[Lang, dict[str, str]]):
        self._translations = translations

    @staticmethod
    def _get_dict_items(data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in Translator._get_dict_items(value):
                    yield f"{key}.{sub_key}", sub_value
            else:
                yield key, value

    @classmethod
    def load(cls):
        translations_dir = osp.join(osp.dirname(__file__), "translations")
        translations = {}
        for lang in Lang:
            lang: Lang
            with open(osp.join(translations_dir, f"{lang}.json")) as fh:
                translations[lang] = dict(cls._get_dict_items(json.load(fh)))
        return cls(translations)

    def __call__(
        self, key: str, values: dict = None, *, lang: Lang = DEFAULT_LANG
    ) -> str:
        try:
            return self._translations[lang][key].format(**(values or {}))
        except KeyError:
            raise LookupError(
                f"Missing translation or variable for {key!r} in {lang!r}"
            )
