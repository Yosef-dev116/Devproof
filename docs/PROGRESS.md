# DevProof Progress

## Current Status

**Current Feature**
- `GET /repositories` endpoint completed and tested

**Last Completed**
- GitHub repository created
- Git initialized
- Project folders created
- .gitignore configured
- DEV_GUIDE.md created
- FastAPI backend package created
- `/health` endpoint created
- Local server verified with Uvicorn
- SQLite database foundation created
- Backend startup initializes the SQLite database file
- Local database files ignored by Git
- `repositories` table created
- `repositories` table verified locally
- `RepositoryCreate` Pydantic schema added (`schemas.py`)
- `insert_repository()` added to `database.py` (parameterized `INSERT`)
- `POST /repositories` route added to `main.py`, returns `201 Created`
- Fixed a typo bug: `form backend.app.schemas import ...` → `from ...` (SyntaxError)
- Fixed a typo bug: `INSERT INTO repositrories` → `INSERT INTO repositories` (sqlite3.OperationalError: no such table)
- Endpoint manually tested with `Invoke-WebRequest`:
  - Valid new URL → `201 Created`, returns `{"id": ..., "url": ...}`
  - Duplicate URL → `500 Internal Server Error` (SQLite `UNIQUE` constraint violation, currently unhandled)
  - Missing `url` field → `422 Unprocessable Entity` (automatic Pydantic validation, no custom code needed)
- Discovered local Apache (`httpd`) was already bound to port 8000; ran backend on port 8001 instead rather than stopping Apache
- Duplicate-URL case now handled cleanly: `create_repository` wraps `insert_repository` in `try`/`except sqlite3.IntegrityError`, raising `HTTPException(status_code=409, detail="repository already exists")` instead of letting it crash as a raw `500`
- Verified: duplicate URL now returns `409 Conflict` with `{"detail": "repository already exists"}`; new URLs still return `201 Created` as before
- `RepositoryOut` schema added (`schemas.py`): `id`, `url`, `created_at` — describes the shape of a repository row returned to clients
- `get_all_repositories()` added to `database.py`: runs a `SELECT`, uses `sqlite3.Row` + `dict(row)` to convert each row into a plain dict
- `GET /repositories` route added to `main.py` with `response_model=list[RepositoryOut]`, returns every saved repository as a JSON array
- Verified: returns all previously-inserted repositories with correct `id`, `url`, `created_at` fields

**Next Task**
- Wait for approval before starting the next feature.

---

# Collaboration

Two people now work on this project, asynchronously (whenever each is free). To avoid duplicate work and stay in sync:

- **Branch per task.** Don't commit directly to `main`. Create a branch per feature (e.g. `feature/duplicate-url-handling`), push it, and open a pull request on GitHub when it's ready.
- **Claim a task before starting.** Add your name next to a task in the table below *before* you start working on it, so the other person doesn't pick up the same thing.
- **Review before merging.** The other person looks over the PR (even briefly) before it merges into `main`, so you both know what changed.
- **Update the docs as part of the task, not after.** Whoever finishes a task updates this file (`docs/PROGRESS.md`) *and* the plain-English `What we did so far.md` file (in the separate Github project explanation folder) in the same PR — regardless of who wrote the code.
- **Catch up on the other person's work.** After pulling in commits you didn't write, it's worth having them explained/walked through (e.g. via Claude) before building on top of them, so both of you understand the whole codebase, not just your own half.

## Task Board

| Task | Assignee | Status | Branch |
|---|---|---|---|
| Duplicate-URL handling (`409 Conflict`) | Yosef | Done | (none yet — committed directly to `main`) |
| `GET /repositories` (list all) | Yosef | Done | (none yet — committed directly to `main`) |

(Add a new row per task. Status: Not started / In progress / In review / Done.)

---

# Project Structure

Current folders:

backend/
frontend/
docs/

---

# Decisions Made

- Backend: FastAPI
- Frontend: React + TypeScript + Vite
- Database: SQLite (initially)
- No Docker
- No Redis
- No Celery

---

# What I Learned

## Git

- Git tracks files, not folders.
- Empty folders are ignored.
- `.gitignore` only affects untracked files.
- `.env` should never be committed.

## Project Organization

- Separate frontend and backend.
- Build one feature at a time.
- Understand every feature before moving on.

## FastAPI Backend

- FastAPI defines API routes and runs Python functions for matching requests.
- Uvicorn runs the FastAPI application as a local web server.
- A health endpoint is a simple endpoint used to verify that the backend is running.
- FastAPI automatically converts returned Python dictionaries into JSON responses.
- A Python package folder contains an `__init__.py` file.

## SQLite Database

- SQLite stores data in a local database file.
- Python includes the `sqlite3` module for working with SQLite.
- A database connection is the link between Python code and the database file.
- FastAPI can run setup code when the application starts.
- Generated database files should not be committed to Git.
- A database table defines the shape of one kind of stored data.
- A primary key uniquely identifies each row in a table.
- A unique column prevents duplicate values.
- `CREATE TABLE IF NOT EXISTS` avoids crashing when the table already exists.

## SQL Basics

- SQL is the language used to talk to a database engine like SQLite; `execute()` just hands SQL text to SQLite to run.
- An `INSERT` statement adds a new row; `?` is a placeholder that gets filled in with a separate value.
- **Parameterized queries** (`?` + a tuple of values) keep user input as pure data — it can never be interpreted as SQL syntax, no matter what characters it contains.
- Building SQL by pasting user input directly into the string (e.g. an f-string) lets malicious input change the meaning of the command itself — this is called **SQL injection**, and it's a serious real-world vulnerability.
- A trailing comma (`(url,)`) is required to make a one-element Python tuple; `(url)` without the comma is just `url` in parentheses.

## FastAPI Requests & Validation

- A route parameter typed as a Pydantic model (e.g. `repository: RepositoryCreate`) tells FastAPI to parse and validate the incoming JSON request body against that model.
- If the request body doesn't match the schema (missing/wrong-type fields), FastAPI automatically rejects it with `422 Unprocessable Entity` before the route function body ever runs.
- `status_code=201` on `@app.post(...)` overrides FastAPI's default `200`, since `201 Created` is the correct status for a successful creation.
- `cursor.lastrowid` returns the auto-incremented primary key of the row just inserted.
- A `UNIQUE` column raises `sqlite3.IntegrityError` on a duplicate insert; if uncaught, FastAPI turns any unhandled exception into a generic `500 Internal Server Error`.

## Reading Data & Response Models

- `sqlite3.Row` makes query results accessible by column name (like a dict), instead of plain unlabeled tuples; setting `connection.row_factory = sqlite3.Row` before a `SELECT` enables this.
- `dict(row)` converts a `sqlite3.Row` into a plain Python dict, which FastAPI/Pydantic can then work with directly.
- `response_model=list[RepositoryOut]` on a route tells FastAPI the exact shape of what it returns — it validates and filters the output to match that schema, and documents it automatically (visible at `/docs`).
- A schema used for what a client *sends* (`RepositoryCreate`) and one used for what the server *returns* (`RepositoryOut`) are often different — output can include server-generated fields like `id` and `created_at` that the client never provided.

## Environment / Tooling (Windows/PowerShell)

- PowerShell's `curl` is aliased to `Invoke-WebRequest`, which uses different flags (`-Method`, `-ContentType`, `-Body`) than real curl's `-X`/`-H`/`-d`.
- `netstat -ano | findstr :<port>` shows what's listening on a port; `Get-Process -Id <PID>` identifies which program that is.
- A port conflict (another program already using the port) can produce confusing errors unrelated to your own code — worth checking before assuming a code bug.
- `uvicorn --reload` runs in the foreground and keeps that terminal busy with logs; a second terminal window is needed to send requests while it keeps running.

---

# Questions I Got Wrong

- `.gitignore` does NOT stop tracking already committed files.

---

# Current Goal

Create the first database table for storing GitHub repository records.

Completed.

Stop after this feature.
Do not continue automatically.

---

# Important Decisions Made

- Keep the backend minimal for the first version.
- Use `backend/app/main.py` as the FastAPI application entry point.
- Use `/health` as the first backend endpoint.
- Do not add authentication, GitHub analysis, or frontend integration yet.
- Use Python's built-in `sqlite3` module for the first database foundation.
- Store the local SQLite file at `backend/devproof.db`.
- Keep generated SQLite files out of Git.
- Create a minimal `repositories` table before adding repository API endpoints.
- Store only `id`, `url`, and `created_at` for now.
- Do not add analysis fields until the analysis feature needs them.
- Use `?` parameterized SQL queries everywhere, never f-string/string-formatted SQL, to avoid SQL injection.
- Run the local backend on port 8001 (not 8000) since local Apache (`httpd`) already occupies port 8000; left Apache untouched rather than stopping it.
- Duplicate-URL handling implemented: caught in `main.py` (not `database.py`), keeping `database.py` free of any HTTP/FastAPI knowledge.

---

# Notes

(Add any personal notes here.)
