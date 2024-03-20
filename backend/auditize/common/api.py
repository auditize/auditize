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
