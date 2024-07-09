#!/bin/sh

set -e
set -x

# Build frontend and copy assets to the backend
(cd frontend && npm run build)
mkdir -p backend/src/auditize/data/html
cp -r frontend/dist/* backend/src/auditize/data/html

# Build the backend
(cd backend && rm -rf build && python -m build --wheel)
