# AgentGuard Frontend

React + Vite + Tailwind CSS dashboard for the AgentGuard reliability engine.
Talks to the FastAPI backend in `../backend`.

## Setup

```bash
cd frontend
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if the backend isn't on :8000
npm run dev
```

The dev server runs on `http://localhost:5173`, which is already in the
backend's default CORS allow-list (`backend/app/core/config.py`). Start the
backend first (`uvicorn app.main:app --reload --port 8000` from `backend/`)
so the navbar's "API connected" indicator turns green.

## What's implemented so far

- **Dashboard** (`/`) — agent/tool counts and a risk-level breakdown, computed
  live from `GET /api/agents`.
- **Agent Configuration** (`/agents`, `/agents/new`, `/agents/:agentId`) —
  full create/edit flow for agents and their tools, wired to
  `backend/app/api/agents.py`.

The remaining workflow pages (Scenario Generation, Test Execution, Test
Results, Failure Details, Reliability Report, Regression) are scaffolded
with routing, nav, and layout, but intentionally show an empty state
rather than mocked data until their backend calls are wired up in later
build sections. The Regression page's backend endpoint
(`GET /api/agents/{agent_id}/regression`) already exists — it's next in
line to connect.

## Project structure

```
src/
  api/          Axios instance + per-resource API wrappers
  components/
    layout/     Sidebar, Navbar, Layout shell, ComingSoon stub
    ui/         Button, Card, StatusBadge, ProgressBar, Table, Modal, ...
    charts/     Recharts wrappers (TrendLine, CategoryBars)
    trace/      TraceTimeline (generic execution-trace renderer)
  pages/        One file per route; agent pages live in pages/agents/
  utils/        Shared constants (risk levels, failure categories, nav) and formatters
```
