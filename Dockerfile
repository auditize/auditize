FROM ubuntu:24.04

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
