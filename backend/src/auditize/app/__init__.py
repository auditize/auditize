from fastapi import FastAPI

from auditize.app.app_api import app as api_app
from auditize.app.app_static import app as static_app

__all__ = "app", "api_app"

app = FastAPI()
app.mount("/api", api_app)
app.mount("/", static_app)
