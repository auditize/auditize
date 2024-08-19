serve:
	mkdocs serve -a localhost:8600

redoc:
	python -m auditize openapi > openapi.json
	npx @redocly/cli build-docs openapi.json --output docs/api.html
	rm openapi.json

build: redoc
	mkdocs build

serve-build:
	cd site && python -m http.server 8601
