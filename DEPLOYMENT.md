# AgentGuard — Deployment & Local Development Guide

- Frontend → **Vercel**
- Backend → **Render** (primary instructions) or **Railway** (equivalent, noted inline)
- Database → **SQLite** for local dev, **Postgres** for deployment (see "Database" below for why)

---

## 1. Environment variables — full reference

### Backend (`backend/.env`, copied from `backend/.env.example`)

| Variable | Required | Example | Notes |
|---|---|---|---|
| `LLM_PROVIDER` | yes | `gemini` | `openai` or `gemini` |
| `OPENAI_API_KEY` | only if `LLM_PROVIDER=openai` | `sk-...` | **secret** — never commit, never send to frontend |
| `OPENAI_MODEL` | no | `gpt-4o-mini` | |
| `GEMINI_API_KEY` | only if `LLM_PROVIDER=gemini` | `AIza...` | **secret** — get a free key at https://aistudio.google.com/apikey |
| `GEMINI_MODEL` | no | `gemini-3.6-flash` | Google retires model names often — if you get a 404 "no longer available," the error message names the replacement; update this and redeploy |
| `DATABASE_URL` | yes | `sqlite:///./agentguard.db` (local) or `postgresql://user:pass@host:5432/db` (deployed) | see "Database" section |
| `CORS_ORIGINS` | yes | `http://localhost:5173,https://your-app.vercel.app` | comma-separated, no `*` allowed |
| `LOG_LEVEL` | no | `INFO` | `DEBUG`\|`INFO`\|`WARNING`\|`ERROR` |

`PORT` is **not** something you set yourself — Render/Railway inject it automatically at runtime, and the start command (`--port $PORT`) reads it. Don't add it to `.env`.

### Frontend (`frontend/.env`, copied from `frontend/.env.example`)

| Variable | Required | Example | Notes |
|---|---|---|---|
| `VITE_API_BASE_URL` | yes | `http://localhost:5000` (local) or `https://agentguard-backend.onrender.com` (deployed) | **Not a secret** — this is just the backend's public URL. No API keys ever live here. |

**Do not expose API keys to the frontend.** This is already true by construction: `OPENAI_API_KEY`/`GEMINI_API_KEY` only ever exist in `backend/.env` and are read by `app/core/config.py` server-side. The frontend never receives, stores, or sends them — every LLM call happens inside the backend, and the frontend only ever talks to your own `/api/...` routes. There is nothing to "hide" via build tricks; the key simply never enters frontend code, bundle, or network requests.

---

## 2. Database — what to actually use

The prototype defaults to **SQLite**, which is genuinely the simplest option and is fine for **local development**. For a **deployed** hackathon submission, switch to **Postgres** instead, because most free-tier hosts (including Render's free web service tier) use an *ephemeral filesystem* — anything written to disk, including a SQLite `.db` file, is wiped on every redeploy or restart. If a judge revisits your demo a few hours later and the backend happened to restart, your data (agents, scenarios, test runs) would be gone.

**Render's free Postgres tier** is the simplest reliable fix: a few clicks, a connection string you paste into `DATABASE_URL`, and it persists independently of your web service's lifecycle. That's what `render.yaml` (included) provisions automatically if you use the Blueprint path below.

No code changes are needed to switch — `DATABASE_URL` is the only thing that changes, and `app/core/database.py` already detects and handles both SQLite and Postgres URLs (including normalizing Render/Railway's `postgres://` URLs to the `postgresql://` scheme SQLAlchemy requires).

---

## 3. Local development

### Backend
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
copy .env.example .env      # Windows
# cp .env.example .env      # Mac/Linux

# Edit .env: set LLM_PROVIDER and the matching API key.
# Leave DATABASE_URL as the SQLite default for local dev.

uvicorn app.main:app --reload --reload-dir app --port 5000
```
Verify: open `http://localhost:5000/api/health` → `{"status": "ok"}`, and `http://localhost:5000/api/llm/test` → `"ok": true`.

### Frontend
```bash
cd frontend
npm install
copy .env.example .env      # Windows
# cp .env.example .env      # Mac/Linux
# .env already points at http://localhost:5000 by default — adjust if
# your backend runs on a different port.

npm run dev
```
Open `http://localhost:5173`.

### Run the backend test suite
```bash
cd backend
pytest -v
```

---

## 4. Deploy the backend (Render)

### Option A — Blueprint (one click, uses the included `render.yaml`)

1. Push this repo to GitHub (if not already).
2. In Render: **New → Blueprint** → connect your repo → Render reads `backend/render.yaml` automatically.
3. When prompted for secrets (`OPENAI_API_KEY`/`GEMINI_API_KEY`, `CORS_ORIGINS`), paste your real values. Leave `CORS_ORIGINS` blank for now — you'll come back and set it after deploying the frontend (step 6 below).
4. Click **Apply** — Render provisions both the free Postgres database and the web service, and wires `DATABASE_URL` between them automatically.
5. Wait for the build to finish, then note your backend's URL, e.g. `https://agentguard-backend.onrender.com`.

### Option B — Manual dashboard setup (no Blueprint)

1. **New → PostgreSQL** → create a free database → copy its **Internal Connection String**.
2. **New → Web Service** → connect your repo → set **Root Directory** to `backend`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment**, add every variable from the Backend table in section 1, using the Postgres connection string from step 1 for `DATABASE_URL`. Leave `CORS_ORIGINS` as a placeholder for now.
6. Deploy. Note the resulting URL (e.g. `https://agentguard-backend.onrender.com`).

### Railway equivalent (either option above)
Railway auto-detects `Procfile` and `.python-version` in this repo, so the flow is: **New Project → Deploy from GitHub repo** → set **Root Directory** to `backend` → add a **PostgreSQL** plugin (Railway wires `DATABASE_URL` in automatically) → add the remaining env vars from section 1 under **Variables**. Railway assigns `PORT` automatically, matching the `Procfile`'s `$PORT`.

---

## 5. Deploy the frontend (Vercel)

1. In Vercel: **Add New → Project** → import this repo.
2. **Root Directory**: `frontend`
3. Framework preset: Vercel auto-detects **Vite** — build command `npm run build`, output directory `dist`. Leave defaults.
4. Under **Environment Variables**, add:
   ```
   VITE_API_BASE_URL = https://agentguard-backend.onrender.com
   ```
   (use your actual backend URL from step 4)
5. Deploy. Vercel gives you a URL like `https://agentguard.vercel.app`.

`vercel.json` (included) rewrites all routes to `index.html`, which React Router needs — without it, refreshing on any page other than the homepage would 404.

---

## 6. Wire CORS — the last step (order matters)

You now have both URLs. Go back to your **backend's** environment variables (Render/Railway dashboard) and set:
```
CORS_ORIGINS=https://agentguard.vercel.app
```
(comma-separate additional origins if needed, e.g. to also keep `http://localhost:5173` working for local testing against the deployed backend). Save — this triggers an automatic redeploy of just the backend, no code change needed.

This order (backend first, frontend second, then circle back to set CORS) is necessary because the frontend's URL doesn't exist until after its own first deploy.

---

## 7. Verify the deployed app end-to-end

1. Visit `https://<your-backend>.onrender.com/api/health` → should return `{"status": "ok"}`
2. Visit `https://<your-backend>.onrender.com/api/llm/test` → should return `"ok": true`
3. Visit your Vercel URL → create an agent, generate scenarios, run a test — same flow as local dev, now live.

If step 3 fails with a CORS error in the browser console, double check the `CORS_ORIGINS` value exactly matches your Vercel URL (including `https://`, no trailing slash).
