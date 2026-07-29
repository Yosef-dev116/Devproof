# DevProof — Collaborator Guide

This file is written so you (or an AI assistant you're using, like Codex) can get full context on this project quickly. Read this before writing any code.

---

## What DevProof is

DevProof is a pitch-competition MVP: **enter a GitHub username → pick one of their public repos → get an AI-generated, evidence-based engineering readiness report** (a "credit score for software engineers" — multi-category scores, strengths, weaknesses, evidence, recommendations, a learning roadmap). The pitch deadline is days away — prioritize the demo-critical path over polish. The full spec/gap analysis lives in project memory as `devproof_pitch_spec`/`devproof_deadline` if you're using Claude; ask Yosef if you need the full text.

The core flow is built and working end-to-end (backend + frontend), verified against real GitHub usernames/repos. What's likely still missing when you read this: visual styling (currently plain HTML) and rate-limit hardening — check `docs/PROGRESS.md`'s "Next Task" for the current honest state.

## Tech stack (fixed decisions — don't introduce alternatives)

- **Backend:** Python, FastAPI
- **Frontend:** React, TypeScript, Vite
- **Database:** SQLite (file-based, no separate server)
- **AI:** OpenAI API (`gpt-4o-mini` by default — see `backend/app/ai_report.py`)
- **External API:** GitHub REST API
- **Auth:** "Sign in with GitHub" (OAuth), cookie-based sessions stored in SQLite. Each user only sees their own analyzed repos.
- **Explicitly not using:** Docker, Redis, Celery, payments — keep it to the MVP scope.

## Project structure

```
backend/
  app/
    main.py           — FastAPI app + routes (entry point)
    database.py       — SQLite connection + queries (no FastAPI/HTTP code here)
    schemas.py        — Pydantic models used to validate request/response bodies
    github_client.py  — calls GitHub's REST API (repo info, commits, tree, README, user's repo list), using the shared server-wide GITHUB_TOKEN — not per-user
    auth.py            — GitHub OAuth login-URL building, code exchange, profile fetch (no FastAPI/HTTP code here, mirrors github_client.py's style)
    analysis.py        — pure signal detection from a file-path list (tests/CI/Dockerfile/etc.), no I/O
    code_quality.py    — pure type-safety/"AI slop" heuristics from sampled source file contents, no I/O
    scoring.py         — pure credibility score calculation (stars/forks/commits formula), no I/O
    ai_report.py        — calls OpenAI to generate the evidence-based repo report, no I/O besides the API call itself
    resume_parser.py   — extracts text from an uploaded resume (PDF via pypdf, DOCX via python-docx)
    resume_report.py   — calls OpenAI to compare resume claims against GitHub evidence (separate schema/prompt from ai_report.py)
  requirements.txt
  .env.example       — documents required env vars (OPENAI_API_KEY, GITHUB_TOKEN, GITHUB_OAUTH_CLIENT_ID/SECRET); copy to .env and fill in your real values
docs/
  PROGRESS.md            — technical changelog, decisions, task board
  COLLABORATOR_GUIDE.md   — this file
frontend/  — React + TypeScript + Vite app
```

**Architecture rule:** `database.py` only talks to SQLite. It never imports FastAPI or raises HTTP-related errors. Any translation from a database error (e.g. duplicate row) into an HTTP response (e.g. `409 Conflict`) happens in `main.py`. Keep that separation — don't collapse the layers.

## Local setup

```powershell
cd backend
pip install -r requirements.txt
```

Create `backend/.env` (git-ignored, never commit it):

```
OPENAI_API_KEY=your-real-key-here
GITHUB_TOKEN=your-github-personal-access-token-here
GITHUB_OAUTH_CLIENT_ID=your-github-oauth-client-id-here
GITHUB_OAUTH_CLIENT_SECRET=your-github-oauth-client-secret-here
```

`main.py` loads this automatically on startup via `python-dotenv`. `OPENAI_API_KEY` is required for `/repositories/{id}/analyze` (the `/fetch` and list/CRUD endpoints don't need it). `GITHUB_TOKEN` is optional but strongly recommended — without it, GitHub API calls are capped at 60/hour total; with a token (no special scopes needed for public repo reads), that jumps to 5000/hour. Generate one at `github.com/settings/tokens`.

`GITHUB_OAUTH_CLIENT_ID`/`GITHUB_OAUTH_CLIENT_SECRET` are required for "Sign in with GitHub" — every route except `/health` and `/auth/*` requires a logged-in session. Create an OAuth App at `github.com/settings/developers` → OAuth Apps → New OAuth App, with Homepage URL `http://localhost:5180` and Authorization callback URL `http://localhost:8002/auth/github/callback`. Use `localhost` (not `127.0.0.1`) consistently — the session cookie is host-scoped, so mixing the two breaks login silently.

Run the server from the repo root (not from inside `backend/`), since imports use the `backend.app.` prefix:

```powershell
uvicorn backend.app.main:app --reload --port 8002
```

Port 8002 is the standard local dev port for this project — 8000 may be occupied locally (e.g. by Apache/XAMPP), and 8001 ran into an unrelated stuck-socket issue during development. Use whichever free port makes sense on your machine, just update the frontend's fetch URLs (`frontend/src/`) and the backend's CORS `allow_origins` in `main.py` to match if you change it.

The SQLite database file (`backend/devproof.db`) is created automatically on server startup. It's git-ignored — never commit it.

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

This starts the Vite dev server at `http://localhost:5180` (pinned in `vite.config.ts` — not Vite's default 5173, chosen to avoid clashing with other unrelated projects that may already use 5173 on your machine). The backend's CORS settings (in `main.py`) allow requests from that origin — if you change the port, update both `vite.config.ts` and `allow_origins`.

## Current state of the project

Full technical history and decisions are tracked in `docs/PROGRESS.md` — read that file for the up-to-date list of what's built, what's in progress, and what's explicitly deferred. Don't duplicate that history here; check there first.

## How we work together (read this before picking up a task)

- **Claim a task first.** `docs/PROGRESS.md` has a "Task Board" table. Add your name to a task there *before* starting it, so we don't both build the same thing.
- **Branch per task, no direct commits to `main`.**
  ```
  git checkout main
  git pull
  git checkout -b feature/<short-task-name>
  ```
- **Open a Pull Request when done**, don't merge straight to `main`. The other person reviews it first.
- **Update the docs in the same PR.** When you finish a task, update:
  - `docs/PROGRESS.md` (technical: what changed, new concepts, decisions)
  - the plain-English "What we did so far" file (kept outside the repo, in a shared folder — ask Yosef for it if you need to update it)
- **Parameterized SQL only.** Never build SQL queries with f-strings/string formatting — always use `?` placeholders with a separate values tuple. This is a fixed project rule, not a suggestion (prevents SQL injection).
- **One feature at a time, don't scope-creep.** Don't add extra endpoints or "nice to have" extras beyond the specific task you claimed.

## Note on `DEV_GUIDE.md`

There's also a `DEV_GUIDE.md` in the repo root — that's Yosef's personal learning framework for working with his AI assistant (explain-before-code, quizzes, one feature at a time, etc.). You don't need to follow that exact teaching process yourself, but the underlying engineering rules in it (clean architecture, no unnecessary complexity, stop and confirm before jumping to the next feature) apply to anyone contributing to this repo.
