# Wingman

An AI operating system: objectives in, coordinated actions out. Say "I'm going to Goa
next month" and Wingman's Planner Agent classifies the intent and produces a concrete
plan instead of just replying conversationally.

## What's implemented right now

- **Auth**: register / login / refresh / current-user, JWT-based
- **Chat → Planner Agent → Task pipeline**: every message is treated as an objective;
  the Planner Agent classifies intent (`travel` / `task` / `reminder` / `general`) and
  returns a step-by-step plan. Runs on keyword heuristics with zero config, or on Claude
  if you set `ANTHROPIC_API_KEY`.
- **Tasks, Trips, Reminders**: basic CRUD, wired to the DB
- **Frontend**: Next.js dashboard — chat on the left, live "flight plan" readout on the right

## Not implemented yet (see Part 2/3 of the original spec for the full scope)

- Multi-agent LangGraph orchestration (currently a direct service call — see the
  docstring in `backend/services/chat_service.py` for the extension point)
- RAG / Document Agent / ChromaDB ingestion pipeline
- Reminder Agent's actual scheduling/notification delivery (rows are created, nothing
  fires them yet)
- OAuth login

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` if you don't have it)
- Node.js 20+
- Docker Desktop (for Postgres + Redis)
- VS Code with the extensions in `.vscode/extensions.json` (VS Code will prompt you to
  install these automatically when you open the folder)

## Setup

### 1. Start the database

```bash
docker compose up -d
```

This starts Postgres on `5432` and Redis on `6379` with the credentials already baked
into `backend/.env.example`.

### 2. Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run alembic revision --autogenerate -m "initial schema"
uv run alembic upgrade head
uv run uvicorn backend.main:app --reload --port 8000
```

API docs: http://localhost:8000/api/docs

To enable LLM-backed planning instead of the keyword heuristic, add this to
`backend/.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

## Running in VS Code

1. Open the `wingman/` folder as your VS Code workspace root (**not** `backend/` or
   `frontend/` individually — the launch configs assume the root).
2. Install the recommended extensions when prompted (Python, Black, ESLint, Prettier,
   Tailwind CSS IntelliSense).
3. Create the backend virtual environment so the Python extension can find it:
   ```bash
   cd backend && uv sync
   ```
   This creates `backend/.venv`, which `.vscode/settings.json` already points VS Code at.
4. Run `docker compose up -d` once (Command Palette → **Tasks: Run Task** →
   `Docker: start Postgres + Redis`, or just run it in a terminal).
5. Open the **Run and Debug** panel (`Cmd/Ctrl+Shift+D`) and pick a configuration from
   the dropdown:
   - **Run Wingman (backend + frontend)** — starts both servers together, the fastest way
     to just try the app
   - **Backend: FastAPI (uvicorn)** — backend only, with breakpoints working
   - **Frontend: Next.js dev server** — frontend only
   - **Backend: Pytest (current file)** — open a test file first, then run this to debug it
6. Hit the green ▶ Run button (or `F5`).

Other common commands are available via **Terminal → Run Task**: installing deps,
running migrations, running the full test suite.

## Project structure

See `backend/` and `frontend/` — layout follows the layered architecture (routes →
services → repositories → database) described in the project's engineering spec.

## Tests

```bash
cd backend
uv run pytest -v
```
