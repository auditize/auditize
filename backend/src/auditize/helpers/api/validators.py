import re

IDENTIFIER_PATTERN_STRING = r"^[a-z0-9_-]+$"
IDENTIFIER_PATTERN = re.compile(IDENTIFIER_PATTERN_STRING)