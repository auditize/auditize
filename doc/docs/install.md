# Installation

This installation documentation is voluntarily limited to a Docker & Docker Compose environment installation and does not cover :

- the deployment of a production-grade HTTP Reverse Proxy such as Nginx or Apache,
- nor the setup of a TLS termination.

This documentation must be considered as a starting point to get a local Auditize instance up and running, understand how it works and how you could deploy it in a production environment.

This page will guide you through the installation of a Docker Compose environment built from the Auditize source repository. This environment will include the following services:

- mongodb
- auditize-web (API & frontend)
- auditize-scheduler (period tasks scheduler)

Auditize uses MongoDB as a database and do not use the filesystem to persist data. The MongoDB data is stored in a Docker volume named `auditize_mongo-data` (as it is should be seen by the `docker volume ls` command).

## Requirements

- Linux or macOS (Windows & WSL2 not tested)
- Docker & Docker Compose (or Docker Desktop)
- Git (optional but recommended, you can still download the git repository as a zip file from GitHub)
- GNU Make (optional but widely available and recommended, you can run still the underlying `Makefile` commands manually)

## Build and run the Docker environment

### Clone the repository

```bash
git clone git@github.com:auditize/auditize.git
```


### Go to the Auditize's Docker directory

```bash
cd auditize/docker
```


### Build the Auditize Docker image
  
```bash
make build
```

### Setup the `.env` file

The Auditize base configuration is 100% environment variables based. It makes it easy and flexible to configure Auditize, especially in a Docker environment.

In the `docker` directory, you'll find a `.env.example` file which serve as a template for the environment variables. You can copy this file to `.env` and modify it as needed. The configuration is documented in details [here](config.md).

Make sure that the `.env` file contains at least the **required environment variables**.

### Run docker compose

Start the Docker containers:

```bash
make up
```

### Access Auditize

When Auditize is run for the first time on an empty database, it will create a default superadmin user with:

- email: `super.admin@example.net`
- password: `auditize`

You can now access the Auditize web interface at [http://localhost:8080](http://localhost:8080) with the credentials above. For security concerns, it is of course recommended to create a brand new superadmin user to your own identity and then **delete the default one**.

### Other useful make commands

- `make down` to stop the Auditize services
- `make logs` to display the logs of the Auditize services (excluding MongoDB)
