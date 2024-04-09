from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic
from pymongo.errors import DuplicateKeyError

from auditize.logs.api import router as logs_router
from auditize.repos.api import router as repos_router
from auditize.common.exceptions import UnknownModelException
from auditize.common.api import make_404_response, make_409_response
from auditize.common.mongo import database

ic.configureOutput(includeContext=True)

app = FastAPI()

# Allow CORS for the frontend (FIXME: make this configurable)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def setup_db():
    await database.setup()


# Add exception handlers

@app.exception_handler(UnknownModelException)
def resource_not_found_handler(request, exc):
    return make_404_response()


@app.exception_handler(DuplicateKeyError)
def duplicate_key_handler(request, exc):
    return make_409_response()


app.include_router(logs_router)
app.include_router(repos_router)
