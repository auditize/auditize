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

# Build the project
COPY . /src
RUN cd /src && . "/root/.nvm/nvm.sh" && ./build.sh

FROM python:3.12 AS run

EXPOSE 80

COPY --from=build /src/backend/dist /dist

RUN pip install /dist/*.whl

CMD ["sh", "-c", "python -m auditize bootstrap_superadmin && uvicorn auditize.main:app --host 0.0.0.0 --port 80"]
