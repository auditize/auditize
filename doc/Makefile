serve:
	mkdocs serve -a localhost:8600

openapi:
	python -m auditize openapi > docs/openapi.json

build: openapi
	mkdocs build

serve-build: build
	cd site && python -m http.server 8601
