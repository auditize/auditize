# Shortcut for ASGI server, the entrypoint is: auditize:asgi
from .app import app_factory as asgi

__version__ = "0.2.4"
