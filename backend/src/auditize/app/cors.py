from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI, *, cors_allow_origins: list[str]):
    if not cors_allow_origins:
        return

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
