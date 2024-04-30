from fastapi.responses import JSONResponse
from pydantic import BaseModel


class NotFoundResponse(BaseModel):
    detail: str = "Not found"


COMMON_RESPONSES = {
    404: {
        "description": "Not found",
        "model": NotFoundResponse
    }
}


def make_404_response():
    return JSONResponse(status_code=404, content={"detail": "Not found"})


def make_409_response():
    return JSONResponse(status_code=409, content={"detail": "Resource already exists"})


def make_401_response():
    return JSONResponse(status_code=401, content={"detail": "Unauthorized"})


def make_403_response():
    return JSONResponse(status_code=403, content={"detail": "Forbidden"})
