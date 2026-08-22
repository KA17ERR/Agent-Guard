@echo off
REM Starts the AgentGuard backend (FastAPI) and frontend (Vite) together.
REM Usage: start.bat

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend
set FRONTEND_DIR=%ROOT_DIR%frontend

REM --- Backend setup ---
cd /d "%BACKEND_DIR%"
if not exist venv (
  echo Creating backend virtual environment...
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install -q -r requirements.txt
call venv\Scripts\deactivate.bat

if not exist .env (
  echo No backend .env found - copying from .env.example.
  echo Edit backend\.env and add your real API key before generating scenarios.
  copy .env.example .env
)

echo Starting backend on http://localhost:8000
start "AgentGuard Backend" "%ROOT_DIR%run_backend.bat"

REM --- Frontend setup ---
cd /d "%FRONTEND_DIR%"
if not exist node_modules (
  echo Installing frontend dependencies, first run only.
  call npm install
)
if not exist .env (
  copy .env.example .env
)

echo Starting frontend on http://localhost:5173
start "AgentGuard Frontend" "%ROOT_DIR%run_frontend.bat"

echo.
echo Two windows have opened: AgentGuard Backend and AgentGuard Frontend.
echo Close both windows to stop the app.
