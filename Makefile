build:
	# Build the frontend
	cd frontend && npm install && npm run build
	# Copy the frontend build to the backend static dir
	mkdir -p backend/src/auditize/data/html
	rm -rf backend/src/auditize/data/html/*
	cp -r frontend/dist/app/* backend/src/auditize/data/html
	cp frontend/dist/lib/auditize-web-component.mjs  backend/src/auditize/data/html
	# Build the backend
	cd backend && rm -rf build && python3 -m build --wheel
	ls -lh ${PWD}/backend/dist/*.whl
