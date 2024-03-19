from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic

from auditize.logs.api import router as logs_router

ic.configureOutput(includeContext=True)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(logs_router)
