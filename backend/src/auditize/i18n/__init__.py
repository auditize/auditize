from .detection import get_request_lang
from .translator import Translator

__all__ = ("t", "get_request_lang")

t = Translator.load()
