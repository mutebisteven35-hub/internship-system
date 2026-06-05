#!/usr/bin/env bash
set -o errexit

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$PROJECT_DIR"
python -m pip install -r backend/requirements.txt

if command -v npm >/dev/null 2>&1; then
  cd "$PROJECT_DIR/frontend"
  npm install
  VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api}" VITE_BASE_PATH="${VITE_BASE_PATH:-/static/frontend/}" npm run build
else
  echo "npm was not found; skipping React build. Install Node.js or build frontend/dist before collectstatic."
fi

cd "$PROJECT_DIR/backend"
python manage.py collectstatic --noinput
python manage.py migrate
