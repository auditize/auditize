from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from icecream import ic

from auditize.logs.api import router as logs_router
from auditize.common.exceptions import UnknownModelException
from auditize.common.api import make_404_response

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


# Add exception handlers
@app.exception_handler(UnknownModelException)
def resource_not_found_handler(request, exc):
    return make_404_response()


app.include_router(logs_router)
