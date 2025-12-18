build-frontend:
	cd frontend && npm install && npm run build

copy-frontend: build-frontend
	mkdir -p backend/src/auditize/data/html
	rm -rf backend/src/auditize/data/html/*
	cp -r frontend/dist/app/* backend/src/auditize/data/html
	cp frontend/dist/lib/auditize-web-component.mjs backend/src/auditize/data/html

build-backend:
	# NB: Temporary override the requirements.txt file to include the pinned dependencies from uv.lock
	cd backend && \
		rm -rf build && \
		cp -a requirements.txt requirements.txt.bak && \
		uv export --no-hashes --frozen --no-annotate --no-header --no-editable --no-emit-workspace > requirements.txt && \
		uv build --wheel && \
		mv requirements.txt.bak requirements.txt
	ls -lht ${PWD}/backend/dist/*.whl | head -n 1

build: copy-frontend build-backend

upgrade-backend-deps:
	cd backend && pip-compile -U requirements.in && pip-compile -U requirements-dev.in
	# do not upgrade doc dependencies, just apply constraints
	cd doc && pip-compile requirements.in

upgrade-doc-deps:
	cd doc && pip-compile -U requirements.in
