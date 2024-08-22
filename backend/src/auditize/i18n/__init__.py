from .detection import get_request_lang
from .lang import Lang
from .translator import Translator

__all__ = ("t", "get_request_lang", "Lang")

t = Translator.load()
