from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from auditize.config import get_config


def setup_cors(app: FastAPI):
    config = get_config()
    if not config.cors_allow_origins:
        return

    # FIXME: CORS is currently untested as the app is loaded once the module is imported
    # putting this under tests would require to to build the app through a function.
    # Please note that is directly supported by uvicorn through the --factory option.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
