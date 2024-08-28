FROM ubuntu:24.04 AS build

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl

# Install python dependencies
RUN pip3 install build --break-system-packages

# Install nodejs
RUN curl -o - https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
RUN . "/root/.nvm/nvm.sh" && nvm install 20

# Build the project (front & back)
COPY . /src
RUN cd /src && . "/root/.nvm/nvm.sh" && ./build.sh

FROM python:3.12 AS base

RUN apt-get update

COPY --from=build /src/backend/dist /dist

RUN pip install /dist/*.whl

EXPOSE 8000

RUN groupadd -r auditize-group && useradd -r -m -g auditize-group auditize-user

USER auditize-user

ENTRYPOINT ["python", "-m", "auditize"]
