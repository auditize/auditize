from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator


class RepoCreationRequest(BaseModel):
    name: str = Field(description="The repository name")


class RepoCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The repository ID")
