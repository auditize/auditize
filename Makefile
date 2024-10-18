build-frontend:
	cd frontend && npm install && npm run build

copy-frontend: build-frontend
	mkdir -p backend/src/auditize/data/html
	rm -rf backend/src/auditize/data/html/*
	cp -r frontend/dist/app/* backend/src/auditize/data/html
	cp frontend/dist/lib/auditize-web-component.mjs backend/src/auditize/data/html

build-backend:
	cd backend && rm -rf build && python3 -m build --wheel
	ls -lht ${PWD}/backend/dist/*.whl | head -n 1

build: copy-frontend build-backend

upgrade-backend-deps:
	cd backend && pip-compile -U requirements.in && pip-compile -U requirements-dev.in
	# do not upgrade doc dependencies, just apply constraints
	cd doc && pip-compile requirements.in
