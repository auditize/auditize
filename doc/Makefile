UV_PROJECT = ../backend
export

serve:
	uv run mkdocs serve -a localhost:8600

openapi:
	uv run python -m auditize openapi > docs/openapi.json

build: openapi
	uv run mkdocs build

serve-build: build
	cd site && uv run python -m http.server -b 0.0.0.0 8601
