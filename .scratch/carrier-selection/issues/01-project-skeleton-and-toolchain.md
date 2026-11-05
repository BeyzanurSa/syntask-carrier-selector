# 01: Project skeleton and toolchain

**What to build:** A developer can start the backend and the frontend with two commands and see the dashboard shell talking to the backend. Everything later tickets need is in place: a Python 3.11+ environment, a FastAPI app with a health check, a passing pytest run, a Next.js App Router app with the navy/blue/white/light-gray theme tokens, a sidebar with the five pages (Dashboard, Taşıyıcılar, Yeni Sipariş, Seçim Sonucu, Kurallar) as empty placeholders, TypeScript types generated from the backend's OpenAPI schema, and the secret-handling files. Spec: docs/specs/0001-carrier-selection.md.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Python 3.11+ is installed (with the user's confirmation) and the backend runs in its own virtual environment; the TypeSafe SDK installs cleanly
- [ ] The backend exposes a health endpoint and an empty pytest suite runs green
- [ ] The frontend starts, shows the sidebar with the five pages in Turkish, and the dashboard displays the backend's health status
- [ ] Frontend API types are generated from the backend OpenAPI schema with one documented command
- [ ] `.env.example` lists `TYPESAFE_API_KEY` and the API base URL with placeholders only; `.gitignore` excludes `.env`, virtualenvs, node_modules and the SQLite file
- [ ] The frontend only knows the API base URL; no secret reaches any frontend variable
- [ ] A short CLAUDE.md records the project rules (Jev interprets, code decides; no hardcoded carrier names; test command)
- [ ] (Optional, with the user's OK) the project is a git repository with a first commit
