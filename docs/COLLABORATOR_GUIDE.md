# DevProof — Collaborator Guide

This file is written so you (or an AI assistant you're using, like Codex) can get full context on this project quickly. Read this before writing any code.

---

## What DevProof is

DevProof is a GitHub repository analysis tool — the goal is to give developers an evidence-based "credibility" score derived from their repositories. Right now the project is early-stage: just a backend and a database, built one small feature at a time.

## Tech stack (fixed decisions — don't introduce alternatives)

- **Backend:** Python, FastAPI
- **Frontend:** React, TypeScript, Vite (not built yet)
- **Database:** SQLite (file-based, no separate server)
- **Explicitly not using:** Docker, Redis, Celery — keep the first version simple.

## Project structure

```
backend/
  app/
    main.py       — FastAPI app + routes (entry point)
    database.py   — SQLite connection + queries (no FastAPI/HTTP code here)
    schemas.py    — Pydantic models used to validate request bodies
  requirements.txt
docs/
  PROGRESS.md            — technical changelog, decisions, task board
  COLLABORATOR_GUIDE.md   — this file
frontend/  (empty so far)
```

**Architecture rule:** `database.py` only talks to SQLite. It never imports FastAPI or raises HTTP-related errors. Any translation from a database error (e.g. duplicate row) into an HTTP response (e.g. `409 Conflict`) happens in `main.py`. Keep that separation — don't collapse the layers.

## Local setup

```powershell
cd backend
pip install -r requirements.txt
```

Run the server from the repo root (not from inside `backend/`), since imports use the `backend.app.` prefix:

```powershell
uvicorn backend.app.main:app --reload --port 8001
```

Port 8001 is used instead of 8000 because 8000 may already be occupied locally (e.g. by Apache/XAMPP) on some machines — adjust if it's free on yours.

The SQLite database file (`backend/devproof.db`) is created automatically on server startup. It's git-ignored — never commit it.

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
- **One feature at a time, don't scope-creep.** Don't add authentication, extra endpoints, or "nice to have" extras beyond the specific task you claimed.

## Note on `DEV_GUIDE.md`

There's also a `DEV_GUIDE.md` in the repo root — that's Yosef's personal learning framework for working with his AI assistant (explain-before-code, quizzes, one feature at a time, etc.). You don't need to follow that exact teaching process yourself, but the underlying engineering rules in it (clean architecture, no unnecessary complexity, stop and confirm before jumping to the next feature) apply to anyone contributing to this repo.
