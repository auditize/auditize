from typing import Annotated

from pydantic import BaseModel, Field, BeforeValidator

from auditize.repos.models import Repo, RepoUpdate


class RepoCreationRequest(BaseModel):
    name: str = Field(description="The repository name")

    def to_repo(self):
        return Repo.model_validate(self.model_dump())


class RepoUpdateRequest(BaseModel):
    name: str = Field(description="The repository name")

    def to_repo_update(self):
        return RepoUpdate.model_validate(self.model_dump())


class RepoCreationResponse(BaseModel):
    id: Annotated[str, BeforeValidator(str)] = Field(description="The repository ID")
