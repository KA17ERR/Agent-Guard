# AgentGuard

AI Agent Evaluation and Reliability Engine. See `backend/` (FastAPI) and
`frontend/` (React + Vite) for details on each half.

## Quick start (one command)

**Mac / Linux:**
```bash
chmod +x start.sh   # first time only
./start.sh
```

**Windows:**
```
start.bat
```

Either script will:
1. Create the backend's Python virtual environment and install dependencies, if not already done.
2. Copy `backend/.env.example` → `backend/.env` if you don't have one yet (edit it to add your real OpenAI/Gemini key).
3. Start the backend at `http://localhost:8000`.
4. Run `npm install` for the frontend, if not already done.
5. Start the frontend at `http://localhost:5173`.

Open `http://localhost:5173` once both are running.

- On Mac/Linux, `Ctrl+C` in the terminal stops both servers.
- On Windows, two separate console windows open (Backend, Frontend) — close both to stop.

## Manual start (two terminals)

If you'd rather run them yourself:

```bash
# Terminal 1
cd backend
uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

## Requirements

- Python 3.11+ (for the backend)
- Node.js 18+ (for the frontend)
