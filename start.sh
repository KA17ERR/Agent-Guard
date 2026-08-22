#!/usr/bin/env bash
# Starts the AgentGuard backend (FastAPI) and frontend (Vite) together.
# Usage: ./start.sh
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# --- Backend setup ----------------------------------------------------------
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
  echo "Creating backend virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  echo "No backend/.env found — copying from .env.example."
  echo "Edit backend/.env and add your real API key before generating scenarios."
  cp .env.example .env
fi

echo "Starting backend on http://localhost:8000 ..."
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
deactivate

# --- Frontend setup ----------------------------------------------------------
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies (first run only)..."
  npm install
fi
if [ ! -f ".env" ]; then
  cp .env.example .env
fi

# Make sure the backend gets stopped if this script (or the frontend) exits.
cleanup() {
  echo ""
  echo "Stopping backend..."
  kill "$BACKEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "Starting frontend on http://localhost:5173 ..."
npm run dev
