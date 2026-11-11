# Auditize backend

Python 3.12+ backend of Auditize (audit log management): a FastAPI REST API, an
MCP server and a CLI. Configuration and business data (repos, users, API keys,
permissions, log filters, ...) live in PostgreSQL, logs live in Elasticsearch
(one index per repository).

The repository root also holds `frontend/` (React), `doc/` (MkDocs) and
`docker/`. This file only covers `backend/`.

## Commands

Dependencies are managed with [uv](https://docs.astral.sh/uv/); run everything
from `backend/` through `uv run`.

```bash
uv run pytest                              # whole test suite
uv run pytest -n 4                         # in parallel (pytest-xdist)
uv run pytest tests/test_repo_api.py -k name
uv run ruff check                          # import sorting (auto-fixes)
uv run ruff format                         # formatting
uv run python -m auditize --help           # CLI: serve, migrate-db, reindex, analyze-logs, ...
```

Tests need a running PostgreSQL and Elasticsearch. The simplest way is the
throwaway services of `docker-compose.test.yml`:

```bash
docker compose -f docker-compose.test.yml up -d --wait
docker compose -f docker-compose.test.yml down -v
```

They listen on non-default ports, so the tests need the (non committed)
`.env.test` file described in the header of `docker-compose.test.yml`.
Environment variables take precedence over that file (see
`tests/helpers/config.py`).

## Layout

```
src/auditize/
  __main__.py        CLI entry point (argparse sub-commands)
  config.py          configuration loaded from AUDITIZE_* environment variables
  app/               FastAPI apps: /api (REST), /mcp (MCP), / (static frontend)
  api/               shared API models (pagination, search), validation, error handling
  auth/              authentication (session cookie, API key, access token) and Require* dependencies
  permissions/       permission models, service and assertions (can_read_logs_from_repo, ...)
  database/          DatabaseManager, SQL base models and helpers, Elasticsearch client, Alembic migrations
  log/               log API and service, Elasticsearch index mapping and reindex (index.py)
  repo/ user/ apikey/ log_filter/ log_i18n_profile/ info/   feature packages
  llm_tools/         transport-agnostic log tools exposed to LLMs
  mcp/               MCP server (adapter on top of llm_tools)
  log_analysis/      LLM log analysis agent (Pydantic AI), used by the analyze-logs command
  i18n/              backend translations (translations/en.json, fr.json)
tests/               test_<feature>_api.py / test_<feature>_service.py, helpers/, conftest.py
scripts/             standalone maintenance / data injection scripts
```

`src/auditize/data/` is a build artifact (compiled frontend) and is git-ignored.

## Conventions

- A feature package is split into `api.py` (FastAPI router), `models.py`
  (Pydantic request / response models), `service.py` (business logic, takes
  an `AsyncSession` as first argument) and `sql_models.py` (SQLAlchemy models).
  New routers are registered in `app/app_api.py`.
- Everything is async: SQLAlchemy `AsyncSession` (injected with
  `Depends(get_db_session)`) and `AsyncElasticsearch`.
- Endpoints declare `summary`, `operation_id`, `tags`, `status_code`,
  `response_model` and their error responses with `error_responses(...)`:
  the OpenAPI schema is published in the documentation.
- Authorization is declared on the endpoint with `Require`, `RequireUser`,
  `RequireApikey`, `RequireLogReadPermission`, ... combined with assertions
  from `permissions/assertions.py`.
- Services raise the exceptions of `auditize/exceptions.py` (`NotFoundError`,
  `ValidationError`, `ConstraintViolation`, `PermissionDenied`, ...); the API
  layer turns them into HTTP errors. Database constraint errors are mapped to
  these exceptions through the `constraint_rules` argument of
  `save_sql_model` / `update_sql_model`.
- SQL models inherit from `SqlModel` (plus `HasId`, `HasDates`) and rely on
  its constraint naming convention (`ix_<table>_<column>`,
  `fk_<table>_<column>`, ...).
- User-facing error messages are translated: add the key to both
  `i18n/translations/en.json` and `fr.json`.
- Code, comments and commit messages are in English.

## Things to keep in sync

- **SQL schema change**: add an Alembic revision in
  `database/alembic/versions/` with the regular `alembic` command, run from
  `src/auditize/database/` (where `alembic.ini` lives), e.g.
  `uv run alembic revision --autogenerate -m "add repo reindex progress"`.
  Alembic connects to the database of the Auditize configuration
  (`AUDITIZE_*` environment variables). Tests create their database by running
  the migrations, so a model change without migration fails the test suite.
- **Elasticsearch mapping change**: bump `_MAPPING_VERSION` in `log/index.py`,
  document it in the mapping history comment there, and make sure existing
  indices can be migrated by the `reindex` command (covered by
  `tests/test_log_reindex.py` and the per-version fixtures of
  `tests/data/reindex/`).
- **New configuration variable**: add it to `config.py` and document it in
  `../doc/docs/config.md`.
- **New dependency**: add it to `requirements.txt` (the source of the package
  dependencies, loosely pinned), then run `uv lock`.
- **User-visible change**: add an entry to `../CHANGELOG.md`.

## Tests

- Tests run against real PostgreSQL and Elasticsearch, nothing is mocked. Each
  session creates a randomly named `test_XXXX` database, tables are truncated
  after each test.
- pytest-asyncio runs in `auto` mode: write plain `async def test_...`
  functions, no decorator needed.
- Use the fixtures of `tests/conftest.py`: HTTP clients with given permissions
  (`superadmin_client`, `log_read_client`, `repo_write_client`,
  `no_permission_client`, `anon_client`, ...), builders (`user_builder`,
  `apikey_builder`, `repo_builder`) and prepared objects (`repo`, `user`,
  `apikey`).
- API tests go through `HttpTestHelper` (`tests/helpers/http.py`) and its
  `assert_get` / `assert_post_created` / `assert_patch` / `assert_delete`
  methods, with the `Prepared*` helpers of `tests/helpers/` to create data and
  build the expected responses.
- A new endpoint comes with tests for the nominal case, validation errors and
  permission checks (401 / 403).
