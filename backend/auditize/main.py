from fastapi import FastAPI
from icecream import ic

from auditize.logs.api import router as logs_router

ic.configureOutput(includeContext=True)


app = FastAPI()
app.include_router(logs_router)
