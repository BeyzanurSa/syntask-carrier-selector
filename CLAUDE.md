# Carrier Selector

Case study: picks the best carrier for a container transport Order.

- Glossary: `CONTEXT.md`. Decisions: `docs/adr/`. Spec: `docs/specs/0001-carrier-selection.md`. Tickets: `.scratch/carrier-selection/issues/`.
- `backend/`: FastAPI + SQLModel (Python 3.12, venv in `backend/.venv`). `frontend/`: Next.js 16 App Router + Tailwind + shadcn/ui. Read `frontend/AGENTS.md` before writing Next.js code.

## Rules

- Jev interprets, deterministic code decides (ADR 0001). Jev never selects a carrier or computes a price; thresholds live in Python, not in the Jev adapter.
- Never hardcode carrier names or properties in decision code; carriers come from the database.
- The Rule set lives in `rules.yaml` (ADR 0002). Distances are never estimated (ADR 0003).
- Money is `Decimal` with 2 places, never float.
- The Jev key is read only from `TYPESAFE_API_KEY` in `backend/.env`. Never print, log or commit it, and never read `.env` or text files that may hold keys.
- UI and reason texts are Turkish; code, API fields and status values are English.
- Tests go through the HTTP API (the agreed seam), with only the Interpreter and DistanceProvider faked. No engine-internal tests.

## Commands

- Backend tests: `cd backend && .venv/bin/pytest -q`
- Backend dev server: `cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000`
- Frontend dev server: `cd frontend && npm run dev`
- Frontend checks: `cd frontend && npm run typecheck && npm run lint`
- Regenerate API types after backend schema changes: `cd frontend && npm run gen:api`
