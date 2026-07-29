# DevProof Progress

## Current Status

**Current Feature**
- Each report category now has a click-to-expand "details" explanation (3-5 grounded sentences), not just the 15-word comment

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
- `get_repository_by_id()` added to `database.py`: `SELECT ... WHERE id = ?`, returns `None` if no row matches (via `cursor.fetchone()`)
- `GET /repositories/{repository_id}` route added to `main.py`: path parameter typed as `int`, returns `404 Not Found` with `{"detail": "repository not found"}` if `get_repository_by_id` returns `None`
- Verified: existing ID → `200` with repository data; missing ID → `404`
- `requests` library added to `requirements.txt` for calling the real GitHub API
- `repositories` table extended with new nullable columns: `stars`, `forks`, `language`, `description`, `owner`, `recent_commit_count`, `last_fetched_at`
- New file `backend/app/github_client.py`: `parse_github_url()` extracts owner/repo from a saved URL; `fetch_repo_data()` calls GitHub's REST API (repo info + recent commits) and returns a plain dict
- `update_repository_github_data()` added to `database.py` (parameterized `UPDATE`, sets `last_fetched_at` via `CURRENT_TIMESTAMP`)
- New route `POST /repositories/{repository_id}/fetch` in `main.py`: looks up the repo, parses its URL, calls GitHub, saves the result, returns the updated `RepositoryOut`
- Errors from GitHub are translated to clean HTTP responses: GitHub 404 → our `404 Not Found` ("GitHub repository not found"); any other GitHub API failure → `502 Bad Gateway`
- `RepositoryOut` schema extended with the same new optional fields, all defaulting to `None`
- Local `devproof.db` deleted and regenerated to pick up the new columns (git-ignored test data only, no real data lost)
- Verified live against real GitHub repos: successful fetch populates real stars/forks/description/owner/commit count; a URL pointing to a nonexistent GitHub repo returns `404` and leaves that row's fields `null`

- `delete_repository()` added to `database.py`: parameterized `DELETE`, returns `True`/`False` based on `cursor.rowcount` (whether a row actually matched)
- `DELETE /repositories/{repository_id}` route added to `main.py`, returns `204 No Content` on success, `404 Not Found` if the ID doesn't exist
- Verified: deleting an existing repo returns `204` and removes it from `GET /repositories`; deleting a nonexistent ID returns `404`
- Basic CRUD (create/read/delete) on repositories is now complete
- New file `backend/app/scoring.py`: `calculate_credibility_score(stars, forks, recent_commit_count)` — v1 formula, weighted sum capped at 100:
  ```
  score = min(100, round(stars * 0.01 + forks * 0.02 + recent_commit_count * 2))
  ```
- Score is **computed live on every read**, not stored in the database — always reflects the latest saved `stars`/`forks`/`recent_commit_count`, no separate column or migration needed
- `_attach_credibility_score()` helper added in `main.py`: adds `credibility_score` to a repository dict, `None` if the repo hasn't been fetched from GitHub yet (i.e. `stars` is still `null`)
- Applied to `GET /repositories`, `GET /repositories/{id}`, and `POST /repositories/{id}/fetch` responses
- `RepositoryOut` schema extended with `credibility_score: int | None`
- Verified: unfetched repo → `credibility_score: null`; fetched repo → real number, correctly capped at `100` for a very popular repo (`octocat/Hello-World`, huge stars/forks)

- `frontend/` scaffolded with Vite (`npm create vite@latest . -- --template react-ts`) — React + TypeScript project with a dev server (`npm run dev`) and hot-reloading
- Default Vite starter content (logos, sample counter button, unused CSS/assets) removed and replaced with a minimal `App.tsx` that calls the backend's `/health` endpoint and displays the result
- CORS (`CORSMiddleware`) added to `main.py` — required because browsers block cross-origin requests (different port = different origin) unless the server explicitly allows it
- Verified live in an actual browser (not just curl): the page renders "Backend status: ok", confirming frontend → backend communication works end-to-end
- Local dev port changed from 8001 to **8002**: port 8001 developed a stuck/orphaned socket on this machine (a real process no longer owned it, but Windows kept reporting it as listening) during testing; 8002 is now the standard — see decision below
- `App.tsx` rebuilt into a real UI: a form to add a repository (`POST /repositories`), a table listing all saved repositories with stars/forks/score (`GET /repositories`), and per-row **Fetch** (`POST /repositories/{id}/fetch`) and **Delete** (`DELETE /repositories/{id}`) buttons
- Uses `useState` to hold the repository list, the form's URL input, and any error message; a shared `loadRepositories()` helper re-fetches the list after every add/fetch/delete so the UI always reflects the backend
- `vite.config.ts` pinned to a fixed dev server port (`5180`, `strictPort: true`) instead of Vite's auto-increment behavior — avoids depending on whichever port happens to be free (this machine has other, unrelated projects that also use Vite's default port 5173)
- `main.py`'s CORS `allow_origins` updated to match the fixed frontend port
- Verified fully in a real browser: added a new repo through the UI, confirmed it appeared with empty stats, triggered its GitHub fetch, and confirmed real stars/forks/score appeared after re-render — the complete add → fetch → score loop works through the actual UI, not just direct API calls

- Found via real manual testing (not planned): `POST /repositories/{id}/fetch` returned a generic `502 Bad Gateway` for some repos. Root cause: GitHub's `/repos/{owner}/{repo}/commits` endpoint returns `409 Conflict` (not an empty list) for a repository with zero commits — undocumented-feeling but is GitHub's actual documented behavior. Our code only checked for `404`, so this fell through to the generic `502` branch.
- Fix in `github_client.py`: `fetch_repo_data()` now checks for `status_code == 409` on the commits call specifically and treats it as `recent_commit_count = 0`, instead of raising.
- Fix in `main.py`: the generic `502` error `detail` now includes GitHub's actual returned status code (e.g. `"failed to fetch data from GitHub (GitHub returned 403)"`), so any future failure is diagnosable from the response alone instead of requiring server-side log digging.
- Verified: existing working repos (`octocat/Hello-World`, `fastapi/fastapi`, `psf/requests`) still work correctly after the change; no regression.
- `App.tsx` gained three new pieces of state: `isAdding`, `fetchingId`, `deletingId` — track whether an add/fetch/delete is currently in flight
- Add form: submit button now shows "Adding..." and disables while the request is in flight; Fetch/Delete buttons per row show "Fetching..."/"Deleting..." and disable (both buttons in that row, to prevent overlapping actions on the same repo) while their request is running
- Client-side validation added: a regex (`GITHUB_REPO_URL_PATTERN`) rejects obviously-invalid URLs (missing `https://github.com/owner/repo` shape) before ever sending a request, showing an inline error immediately
- Verified in a real browser: an invalid URL is rejected instantly with no network request; a real fetch correctly shows "Fetching..." with the button disabled mid-flight, then reverts once the real GitHub data lands

**MAJOR PIVOT (2026-07-28): the real pitch-competition MVP spec surfaced.** Everything above was infrastructure; the actual product — username→pick-repo→AI report — hadn't been built. Full spec, gap analysis, and deadline noted in memory (`devproof_pitch_spec`, `devproof_deadline`). Built in this session:

- `github_client.py` gained: `list_public_repos(username)` (`GET /users/{username}/repos`), `fetch_repo_tree(owner, repo, default_branch)` (`GET .../git/trees/{branch}?recursive=1`, returns `[]` on 404/409 for empty repos), `fetch_readme_text(owner, repo)` (`GET .../readme` with raw-content Accept header, `None` on 404). `fetch_repo_data()` now also returns `default_branch`.
- New file `backend/app/analysis.py`: `detect_signals(file_paths)` — pure function scanning file paths for `has_tests`, `has_ci` (`.github/workflows/`), `has_dockerfile`, `has_env_example`, `has_license`, `top_level_entries`, `file_count`. No network/DB/FastAPI code, same "keep layers separate" principle as `scoring.py`.
- New file `backend/app/ai_report.py`: `generate_report(evidence)` calls OpenAI (`gpt-4o-mini`, `response_format={"type": "json_object"}`) with a fixed schema (overall score, 8 categories with name/score/comment, strengths, weaknesses, recommendations, learning roadmap). Raises `AIReportError` on any failure so `main.py` can translate it to a clean `502`, same pattern as GitHub error handling.
- `openai` + `python-dotenv` added to `requirements.txt`; `backend/.env.example` committed (documents `OPENAI_API_KEY=`); real key goes in git-ignored `backend/.env` (confirmed via `git check-ignore` that the existing root `.gitignore` `.env` rule covers it); `main.py` calls `load_dotenv()` at import time.
- `repositories` table extended with `analysis_report TEXT` (JSON-encoded) and `analyzed_at TEXT`; `update_repository_analysis()` added to `database.py`. Local `devproof.db` regenerated again (git-ignored test data only).
- `main.py`: refactored the fetch-and-store logic into `_fetch_and_store_github_data()` (reused by both `/fetch` and the new `/analyze`). New routes: `GET /github/{username}/repos` (404 on unknown user) and `POST /repositories/{repository_id}/analyze` — looks up the repo, always refreshes GitHub data (needed to get `default_branch` reliably anyway), fetches tree + README, runs `detect_signals`, calls `generate_report`, stores and returns the result.
- `App.tsx` rebuilt with the actual required flow: username input → "Load repositories" → simple list with **Select** buttons → clicking one does `POST /repositories` (handling `409` by looking up the existing row instead of failing) → `POST /repositories/{id}/analyze` with an "Analyzing..." loading state → renders the full report (overall score, category scores/comments, strengths, weaknesses, recommendations, learning roadmap). The old direct-URL-entry table stays below as a history view, each row gaining a **View Report** button.
- Verified fully end-to-end, live, twice: `octocat/Hello-World` (empty/tiny repo — correctly scored low, correctly flagged no tests/CI/license) and `fastapi/fastapi` (mature repo — correctly detected tests/CI/license present, scored 85/100). Then verified the *actual UI* end-to-end: typed username `psf`, loaded 20 real repos, clicked Select on `psf/httpbin`, watched "Analyzing..." show, and got back a real, coherent, evidence-grounded report rendered on the page.
- Known limitation: each `/analyze` call takes ~15–30 seconds (4 GitHub calls + 1 OpenAI call) — acceptable for a demo with a loading indicator, but noted here in case it needs optimizing before the pitch.
- "Role Relevance" category is evaluated generically by the model — no target-role input field was added (kept out of scope for the deadline).

**Latency fix — `github_client.py`:**
- Added a module-level `requests.Session()` (`_session`) reused across every GitHub call — avoids repeating TLS handshakes to `api.github.com` on each of the 4+ calls per analysis.
- `fetch_repo_data()` now fetches repo info and commit count **in parallel** (`concurrent.futures.ThreadPoolExecutor`, 2 workers) instead of sequentially.
- New `fetch_tree_and_readme()` fetches the git tree and README **in parallel** (same pattern) — `main.py`'s `/analyze` route now calls this instead of two sequential calls.

**Latency fix — `ai_report.py`:**
- `REPORT_SCHEMA_DESCRIPTION` now caps each category comment at ~15 words and each of the 4 lists (strengths/weaknesses/recommendations/learning_roadmap) at exactly 3 short items — less output to generate, directly cutting OpenAI response time.
- Added `max_tokens=900` as a safety ceiling on the completion.
- README excerpt sent as evidence trimmed from 3000 to 1500 characters (`main.py`).
- **Result:** `/analyze` end-to-end time dropped from ~15-30s to a consistent ~6-8s across multiple real repos, verified by timing curl requests directly.

**Visual styling — frontend:**
- New `frontend/src/App.css`: card-based layout (`.card`), color-coded score badges (`.score-badge` + `.score-high`/`-medium`/`-low`, green/orange/red thresholds at 80/50), styled buttons (`.btn-primary`/`-secondary`/`-danger`/`-small`), styled GitHub repo picker list, two-column strengths/weaknesses layout in the report, styled history table.
- Reuses the existing light/dark CSS variables from `index.css` (`--accent`, `--bg`, `--text`, `--shadow`, etc.) rather than hardcoding colors, so both themes still work.
- Removed leftover fixed-width/centered marketing-page layout from the original Vite scaffold's `#root` rule in `index.css` (was fighting with the new app layout).
- Verified: computed styles checked directly in a live browser tab (border-radius, box-shadow, button colors, score-badge colors change correctly with score value) since this session's screenshot tool was unavailable; then a full live analysis run through the actual styled UI confirmed the report renders correctly end-to-end.

**GitHub API authentication:**
- `github_client.py` reads `GITHUB_TOKEN` from the environment at import time (after `load_dotenv()` has already run in `main.py`, since `github_client` is imported after that call) and attaches it as `Authorization: Bearer <token>` on the shared `_session` if present. No token → falls back to unauthenticated (still works, just at the lower rate limit) — nothing breaks for a collaborator who hasn't set one up yet.
- `backend/.env.example` updated to document the optional `GITHUB_TOKEN` alongside `OPENAI_API_KEY`.
- Verified three ways: (1) confirmed the `Authorization` header is actually present on the session object, (2) called GitHub's own `/rate_limit` endpoint through that same session and confirmed it returns `limit: 5000` (not `60`), (3) ran a full `/analyze` end-to-end afterward to confirm no regression.

**Mobile-responsive styling:**
- `App.tsx`: history table wrapped in a new `.table-scroll` div (`overflow-x: auto`) — HTML tables don't reflow at narrow widths, so this lets it scroll horizontally instead of squishing/breaking.
- `App.css`: added a `@media (max-width: 640px)` block — reduces `.app`/`.card` padding, shrinks the `h1`, stacks `.inline-form` and `.repo-picker-item` vertically (full-width inputs/buttons instead of a cramped row), lets `.row-actions` wrap, and gives `.repo-table` a `min-width: 480px` inside the new scroll wrapper so it scrolls cleanly instead of breaking layout.
- **Verification limitation:** this session's browser-automation tool had a broken `resize_window` (window resize didn't actually change the reported viewport width, `window.innerWidth` stayed at the desktop size regardless) on top of the already-broken screenshot API from earlier in the session. Confirmed instead that the media query rule parses correctly and is present in the loaded stylesheet (`document.styleSheets`), and that both `tsc -b` and a full production `vite build` succeed with no errors. **The actual narrow-viewport visual layout has not been eyeballed this session** — worth a quick manual check (resize the browser window, or DevTools' device toolbar) before relying on it for a demo.

**Bug fix — silent failure when backend is unreachable:**
- Reported by hands-on testing: entering a username and clicking "Load repositories" produced no visible result. Root cause: the backend server had been stopped (as part of test cleanup between features) and never restarted, so the frontend's `fetch()` calls threw a network error that wasn't caught anywhere — the loading state just quietly reset with no message shown.
- Fixed in `App.tsx`: added a `catch` block to `handleAdd`, `handleLoadGithubRepos`, and `handleSelectRepo` — each now sets a clear "Could not reach the backend server. Is it running?" message instead of failing silently. These functions already had `try`/`finally`; this just adds the missing `catch`.
- Immediate fix: restarted the backend (this time with `--reload`, so it survives future code edits without needing a manual restart).
- Recurring environment gotcha (noted for next time): stopping the `uvicorn --reload` **reloader** process (the one `Stop-Process` finds first via `Get-CimInstance ... -match 'uvicorn'`) does not necessarily stop its spawned **worker** child process, which keeps serving requests independently. This has caused "I killed it but it's still responding" confusion multiple times now. When truly stopping the backend, check for `multiprocessing`-spawned child processes too (`Get-CimInstance Win32_Process | Where CommandLine -match 'multiprocessing'`), not just ones matching `'uvicorn'`.

**Bug fix — `.env` silently not loading in the actual running worker process:**
- Reported by hands-on testing: username loading worked, but selecting a repo to analyze failed with "Could not reach the backend server" (a misleading message — see below). The real backend log showed `openai.OpenAIError: Missing credentials ... OPENAI_API_KEY`, even though `backend/.env` genuinely contained a valid key and `GITHUB_TOKEN` from the same file was loading fine.
- Root cause: `load_dotenv()` (called with no arguments in `main.py`) auto-discovers `.env` by walking up from the *caller's file location* using Python stack introspection. That works when `main.py` runs normally, but uvicorn's `--reload` spawns its actual worker process via Windows' `multiprocessing` **spawn** method — a fresh interpreter bootstrap that doesn't preserve the same stack context, so the auto-discovery silently failed to find `backend/.env` specifically in that worker process. Confirmed by writing a throwaway script at the exact same file location (`backend/app/_debug_env_check.py`) — it found the `.env` fine when run directly, but the real uvicorn worker still didn't.
- Fix: `main.py` now calls `load_dotenv(Path(__file__).resolve().parent.parent / ".env")` — an explicit path derived from the module's own `__file__`, immune to how the process was spawned.
- Verified: fully stopped every backend process (reloader + worker), restarted clean, and successfully ran a real `/analyze` call end-to-end against the freshly-spawned worker.
- Separately: while debugging this, `cat -A` was accidentally run on `backend/.env`, printing partial key values into the conversation. User was advised to rotate both `OPENAI_API_KEY` and `GITHUB_TOKEN` as a precaution — **never `cat`/print `.env` file contents directly again; use `dotenv_values()` or check only key names/lengths when inspecting.**

**Unified input (UX simplification):**
- Prompted by user feedback: having two separate boxes ("Analyze a developer's GitHub repository" for a username, "Add a repository directly" for a URL) was confusing — unclear why they were separate, and the first one looked "blank" next to the second one's populated history table.
- `App.tsx` now has a single input + one "Analyze" button. On submit, it checks the input against `GITHUB_REPO_URL_PATTERN`: if it looks like a full repo URL, it goes straight to the add+fetch+analyze pipeline (`addAndAnalyze()`, extracted as a shared helper used both here and by the repo-picker's "Select" buttons); otherwise it's treated as a username and loads that person's repo list, same as before.
- Collapsed `username`/`url`, `usernameError`/`error`, and `isLoadingRepos`/`isAdding` into single `query`, `error`, and `isSubmitting` state variables — the separate direct-add form is gone entirely.
- The old "Add a repository directly" section is now just "Previously Analyzed Repositories" — the history table stays (Fetch/Delete/View Report per row still work), just without its own separate input form.
- Verified both paths through the actual UI: typing a username still loads a real repo list correctly, and pasting a direct repo URL goes straight to a full generated report, both through the same box.

**"Sign in with GitHub" + per-user multi-tenancy:**
- Previously the MVP spec explicitly excluded auth/multi-user (see "Important Decisions Made"). With the pitch deadline close, added it: GitHub OAuth rather than email/password — no password management, fits the product's identity naturally, and doubles as a demo moment.
- New `users`/`sessions` tables in `database.py`; `repositories` gained a `user_id` column and its `url` uniqueness became per-user (`UNIQUE(url, user_id)` instead of a bare `UNIQUE` on `url`) so two different users can add the same repo without colliding. All existing repository functions (`insert_repository`, `get_all_repositories`, `get_repository_by_id`, `update_repository_github_data`, `update_repository_analysis`, `delete_repository`) now take a `user_id` and filter by it.
- New `backend/app/auth.py` (OAuth login-URL building, code exchange, profile fetch) mirrors `github_client.py`'s style: plain functions, `requests`, no FastAPI imports.
- New routes in `main.py`: `GET /auth/github/login`, `GET /auth/github/callback`, `GET /auth/me`, `POST /auth/logout`. Every existing `/repositories*` route and `GET /github/{username}/repos` now requires a logged-in session via a `Depends(get_current_user)` dependency, backed by a cookie-based session stored in SQLite (not an in-memory dict) so logins survive the backend restarts that happen constantly during dev.
- Basic CSRF protection on the OAuth flow: a random `state` value is set in a short-lived cookie by `/auth/github/login` and verified against the callback's `state` query param.
- CORS: added `allow_credentials=True` (required for the session cookie to actually be sent on cross-origin requests from the Vite dev server; the existing `allow_origins` whitelist was already compatible since it isn't `["*"]`).
- Frontend `API_BASE` changed from `http://127.0.0.1:8002` to `http://localhost:8002` — required, not cosmetic. The OAuth callback URL is `http://localhost:8002/...`, so the session cookie is host-scoped to `localhost`; a cookie scoped to `localhost` is never sent on requests to `127.0.0.1`, even on the same machine/port. Missing this would make login look like it worked (the redirect succeeds) while every subsequent API call silently looked logged-out.
- All `fetch()` calls in `App.tsx` now go through a shared `apiFetch()` helper that adds `credentials: 'include'` and resets `currentUser` to `null` on any `401` response, instead of duplicating that logic across all 6 call sites (two of which had no `catch` block at all to piggyback on).
- Deliberately deferred: GitHub *data-fetching* calls (repo info, commits, tree, README, username's repo list) still use the existing shared, process-wide `GITHUB_TOKEN` in `github_client.py` (a single module-level `requests.Session()` with its `Authorization` header set once at import time). Switching those to per-user GitHub OAuth tokens is a real refactor of that module and is out of scope for this feature — OAuth here is only used to identify/scope users, not to make GitHub API calls on their behalf.
- Verified: full DB-layer test (upsert on repeat login, session create/lookup/delete, cross-user repo isolation on list/get/delete, composite unique constraint allowing two users to add the same URL) run directly against `database.py`; full HTTP-layer test against a live `uvicorn` instance (unauthenticated 401s, login redirect + `state` cookie, authenticated `/auth/me` + `/repositories` create/list via cookie, CORS preflight showing `access-control-allow-credentials: true`, logout clearing the session); frontend `tsc -b && vite build` clean; browser screenshots (via Playwright against the real Vite dev server) confirming both the logged-out "Sign in with GitHub" gate and the logged-in avatar/username/logout header with a user-scoped repo list.
- **Update:** this session's Ultraplan-generated patch (`0001addgithuboauthmultitenancy.patch`) was reviewed in full, applied via `git apply`, and independently re-verified: local DB regenerated, backend starts cleanly on the new schema, unauthenticated `/auth/me` and `/repositories` both correctly return `401`, CORS preflight shows `access-control-allow-credentials: true`, and `GET /auth/github/login` correctly builds the GitHub authorize URL with a real `client_id` and sets the `oauth_state` cookie.
- Real GitHub OAuth App created (`github.com/settings/developers`, callback `http://localhost:8002/auth/github/callback`), `GITHUB_OAUTH_CLIENT_ID`/`GITHUB_OAUTH_CLIENT_SECRET` added to `backend/.env`. **Real end-to-end OAuth click-through confirmed working** by the user directly in their own browser: signed in with GitHub, landed back on DevProof authenticated, `users` table shows the real GitHub account, `sessions` table shows an active session.

**"Code Quality & Type Safety (AI Slop)" analysis category:**
- Motivation: catch the specific signature of careless/low-effort AI-generated code — no type hints, no interfaces, `any` everywhere — as its own visible signal, both as a real product feature and (bluntly) so DevProof itself doesn't embarrass anyone if it's run on itself live at the pitch.
- `github_client.py`: `fetch_repo_tree()` now returns `{"path", "size"}` per blob (not just paths) — needed to prioritize substantial files over trivial ones. New `fetch_file_content()`/`fetch_sample_files()` (parallel, same `ThreadPoolExecutor` pattern as the tree/README fetch) pull actual source file contents.
- New `backend/app/code_quality.py` (pure functions, no I/O, same style as `analysis.py`/`scoring.py`): `select_sample_files()` picks up to 6 real source files, biggest-first, capped at 3 per top-level directory, excluding `node_modules/`/`dist/`/`__pycache__/` and trivial filenames (`__init__.py`, `__main__.py`, `setup.py`). `detect_type_safety_signals()` counts Python functions with/without type hints (regex on `def ... ->`/param `:` annotations) and TypeScript/JavaScript interface/type declarations vs. `any` usage.
- **Real bug found and fixed during testing:** the first version of `select_sample_files()` round-robinned by directory without any size awareness, so it picked mostly near-empty `__init__.py` files and docs-site theme JS — causing `tiangolo/sqlmodel` (a library renowned for heavy type annotation) to incorrectly score 40/100 ("limited type hints"). Switched to size-based prioritization; re-verified sqlmodel now correctly scores 90/100 ("Completely type-hinted Python functions, no untyped code"), with the actual sampled file (`sqlmodel/main.py`) showing 62/62 typed functions.
- `ai_report.py`: added as a 9th category in the schema, with explicit prompt guidance to score it from `type_safety_signals` and treat untyped/`any`-heavy/inconsistent code as a low-effort "AI slop" signal even if it otherwise runs.
- No frontend changes needed — the report UI already renders `categories` generically, so the new category just appears.

**DevProof's own repo hygiene (prompted by the AI Slop feature above):** DevProof scored itself 25-36/100 earlier today — almost entirely from missing repo hygiene (no tests, no CI, no LICENSE, a 2-line README), not actual code quality issues.
- Rewrote root `README.md`: real description, features, tech stack, setup instructions, test-running instructions.
- New `backend/tests/`: 15 unit tests across `test_scoring.py`, `test_analysis.py`, `test_code_quality.py`, `test_github_client.py` — all pure-function tests, zero network calls, so they run in CI without needing any API keys. `pytest` added to `requirements.txt`.
- New `.github/workflows/ci.yml`: runs the backend test suite + a frontend production build on every push/PR — DevProof's own analyze pipeline can now genuinely detect `has_ci: true`.
- New `LICENSE` (MIT).
- **Verified the fix worked:** re-ran DevProof's self-analysis after pushing all of the above — overall score went from 25-36 up to **74/100**, with "Code Quality & Type Safety (AI Slop)" itself scoring 90/100 ("All Python functions fully type-hinted"). Remaining drag is just real repo popularity (`Collaboration: 50, "no stars or forks"`) and no Dockerfile — not fixable by more repo hygiene, and not worth chasing further right now.

**Click-to-expand category details:**
- Motivation: the 15-word category comments (e.g. "README lacks detailed usage") were too short to explain themselves — user wanted the actual reasoning and specifics visible per category, not just a one-line verdict.
- `ai_report.py`: each category in the schema now has a `details` field (3-5 real sentences) alongside the existing `comment`, with explicit prompt guidance to (1) name exactly which evidence produced the score, (2) state what's concretely present or missing, and (3) give one specific improvement — and to never let `details` just restate `comment` in longer words.
- `max_tokens` raised from 900 to 2200 to fit the added output. **Latency impact:** `/analyze` went from ~10-13s to ~16-17s. A real, noticeable cost, but judged worth it for the depth requested — flagged here in case it needs revisiting before the pitch.
- Frontend: `ReportCategory` gained `details: string`. Each category row in `App.tsx` is now a clickable button (`expandedCategory` state, one expanded at a time) that toggles showing the full `details` text below it. No backend re-fetch needed — the detail text is already present in the same report payload.
- Verified: real analysis run against `tiangolo/sqlmodel` produced genuinely specific, grounded detail text for all 9 categories (e.g. "All 62 Python functions found... have type hints", "18233 stars and 878 forks", citing the actual evidence rather than generic filler). Click/expand/collapse/switch-between-categories all confirmed working in a live browser tab.

**Next Task**
- Wait for approval before starting the next feature.
- Do a manual visual check of the mobile layout (browser resize or DevTools device toolbar) — not verified live this session due to tooling limitations.
- Optional, not urgent: a Dockerfile would likely push DevProof's own DevOps category score higher, if there's time before the pitch.
- Worth a decision before the pitch: is ~16-17s per analysis acceptable, or should the `details` field be trimmed/shortened if a faster demo matters more than depth?

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
| `GET /repositories/{id}` (single) | Yosef | Done | (none yet — committed directly to `main`) |
| `POST /repositories/{id}/fetch` (GitHub API) | Yosef | Done | (none yet — committed directly to `main`) |
| `DELETE /repositories/{id}` | Yosef | Done | (none yet — committed directly to `main`) |
| Credibility score v1 (stars/forks/commits) | Yosef | Done | (none yet — committed directly to `main`) |
| Frontend scaffold + backend connectivity check | Yosef | Done | (none yet — committed directly to `main`) |
| Frontend UI: add/list/fetch/delete repositories | Yosef | Done | (none yet — committed directly to `main`) |
| Fix: 502 on zero-commit repos | Yosef | Done | (none yet — committed directly to `main`) |
| Frontend UX: loading states + client-side validation | Yosef | Done | (none yet — committed directly to `main`) |
| GitHub username→repo picker + AI report generation (pitch MVP core) | Yosef | Done | (none yet — committed directly to `main`) |
| Visual styling + `/analyze` latency reduction | Yosef | Done | (none yet — committed directly to `main`) |
| GitHub API authentication (60/hr → 5000/hr) | Yosef | Done | (none yet — committed directly to `main`) |
| Mobile-responsive styling | Yosef | Done (visual check pending) | (none yet — committed directly to `main`) |
| Fix: backend-unreachable error message | Yosef | Done | (none yet — committed directly to `main`) |
| Fix: `.env` not loading in `--reload` worker process | Yosef | Done | (none yet — committed directly to `main`) |
| Unified username/URL input (UX simplification) | Yosef | Done | (none yet — committed directly to `main`) |
| "Sign in with GitHub" (OAuth) + per-user multi-tenancy | Yosef | Done | (committed directly to `main`) |
| "Code Quality & Type Safety (AI Slop)" category | Yosef | Done | (committed directly to `main`) |
| DevProof repo hygiene (README/tests/CI/LICENSE) | Yosef | Done | (committed directly to `main`) |
| Click-to-expand category details | Yosef | Done | (committed directly to `main`) |

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
- Auth: "Sign in with GitHub" (OAuth), not email/password — no password management, fits the product's identity naturally, doubles as a demo moment. Cookie-based sessions stored in SQLite, not a JWT/`SessionMiddleware`/in-memory dict.

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
- A route path like `/repositories/{repository_id}` uses `{}` to mark a **path parameter**; FastAPI passes that piece of the URL into the matching function argument, converting it to the type hint given (`int` here).
- `cursor.fetchone()` returns a single row (or `None` if no match), vs. `fetchall()` which returns every matching row as a list — use whichever matches how many results you expect.
- Returning `None` from a database-access function (rather than raising an error) lets the calling route decide how to respond (here: a `404`) — the database layer just reports "found" or "not found," it doesn't decide what that means over HTTP.

## Calling External APIs

- The `requests` library sends real HTTP requests to other servers from Python code, just like a browser or `curl` would.
- `response.raise_for_status()` raises an exception (`requests.HTTPError`) automatically if the response status is an error (4xx/5xx), so failures don't silently get treated as success.
- Separating "talk to an external API" code into its own file (`github_client.py`) keeps the same separation-of-concerns principle used for `database.py` — routes shouldn't know the details of *how* data is fetched, just that a function gives them back a dict.
- Public APIs are often rate-limited (GitHub allows 60 unauthenticated requests/hour per IP) — a real constraint to design around later (e.g. with an API token), not something to ignore in production.
- Adding new nullable columns to an existing table lets a row exist before all its data is known (e.g. a repo exists in our system before we've ever successfully fetched its GitHub data).
- A public API's error responses aren't always intuitive — e.g. GitHub returns `409 Conflict`, not an empty list, for "this repo has no commits yet." Always handle documented edge cases explicitly rather than assuming every non-happy-path case is a clean 404 or empty result.
- Including the underlying error's real status code in your own error message (rather than a single generic message for every non-404 failure) makes future debugging possible without needing server logs.
- `cursor.rowcount` after a `DELETE`/`UPDATE` tells you how many rows were actually affected — useful for knowing whether a `WHERE id = ?` actually matched anything, without a separate lookup.
- `204 No Content` is the correct HTTP status for a successful action that has nothing to return (e.g. a deletion) — the response body stays empty.

## Frontend Basics (Vite + React)

- Vite is a build tool that scaffolds a frontend project and runs a fast dev server with hot-reloading (changes appear instantly without a full page refresh).
- `npm run dev` starts the dev server; `npm run build` compiles a production build (also catches TypeScript errors — useful as a sanity check even before deploying anything).
- React's `useEffect` runs code after the component renders — used here to trigger the `/health` fetch once when the page loads, rather than on every re-render.
- **CORS (Cross-Origin Resource Sharing):** browsers block a webpage from calling an API on a different origin (different port counts as different, even on the same machine) unless that server explicitly allows it via response headers. FastAPI's `CORSMiddleware` adds those headers for origins you list in `allow_origins`.
- A **controlled input** in React (`value={url}` + `onChange`) keeps the input's displayed value in sync with component state, so the current text is always available in JavaScript, not just visible on screen.
- Pinning a dev server to a fixed port (`vite.config.ts` → `server.port` + `strictPort: true`) avoids surprises when other unrelated projects on the same machine also default to the same port.
- After any action that changes backend data (add/fetch/delete), re-fetching the full list is a simple way to keep the UI in sync — no separate "update this one row in place" logic needed for a small app like this.
- A boolean/id piece of state (e.g. `isAdding`, `fetchingId`) tracking "is a request currently in flight" lets the UI show a loading indicator and disable controls to prevent duplicate submissions — a `try`/`finally` ensures that state resets even if the request fails.
- Client-side validation (checking input shape before sending a request) gives instant feedback and avoids an unnecessary round-trip for obviously-invalid input — but it doesn't replace server-side validation (the backend's own Pydantic schema still guards against bad data sent by any other client).

## Derived/Computed Values

- Not every value returned by an API needs to be stored — a value that can always be recalculated from existing data (like a score from `stars`/`forks`/`recent_commit_count`) is simpler to compute on the fly than to keep in sync in the database.
- Keeping the calculation in its own file (`scoring.py`) as a plain function (no database or FastAPI involved) makes it easy to test and easy to change the formula later without touching routes or the database layer.

## Integrating an LLM (OpenAI) into a real feature

- `response_format={"type": "json_object"}` on a chat completion tells the model to return valid JSON, not free-form prose — critical when the response needs to be `json.loads()`-parsed by code, not read by a human.
- Fixing the exact JSON shape in the system prompt (field names, types, category list) makes the model's output reliably structured across calls, instead of varying each time.
- Evidence quality drives output quality: giving the model concrete signals (file paths detected, README text, commit counts) instead of vague context produces specific, grounded claims ("no tests/ directory found") instead of generic filler.
- GitHub's git-tree endpoint (`/git/trees/{branch}?recursive=1`) is the efficient way to get a repo's full file listing in one call, rather than recursively walking the contents API directory by directory.
- An external AI call is just another thing that can fail (network, invalid response, rate limit) — wrap it in its own exception type (`AIReportError`) and translate it to an HTTP error in the route, the same pattern already used for GitHub failures.
- A `python-dotenv` `load_dotenv()` call at process startup reads a local `.env` file into environment variables automatically — avoids needing to export secrets manually in every terminal session.

## Performance: Parallelizing Independent Network Calls

- When two network calls don't depend on each other's results (e.g. fetching a repo's commit count and its basic info), running them in parallel instead of one-after-another cuts wall-clock time roughly in half for that pair.
- `concurrent.futures.ThreadPoolExecutor` is a straightforward way to run a few blocking calls (like `requests.get`) concurrently in ordinary synchronous Python, without needing `async`/`await` everywhere.
- A shared `requests.Session()` reused across multiple calls to the same host avoids repeating the TCP/TLS handshake for every single request — a real, measurable latency win when making several calls to the same API in a row.
- With an AI API call in the pipeline, the model's *output length* is often the biggest lever on latency — asking for shorter, capped-length responses (word limits, fixed list sizes) can meaningfully speed up generation, separate from which model is used.
- Most public APIs (GitHub included) rate-limit unauthenticated requests far more aggressively than authenticated ones — attaching a personal access token via an `Authorization` header is often a five-minute fix for what would otherwise become a real production/demo blocker.
- Verifying "is my token actually being used and accepted" is worth doing explicitly (checking the header is set, then calling the API's own rate-limit/whoami endpoint) rather than assuming it works just because no error was thrown.

## Sampling Real Code for Analysis

- A file's byte size is a much better proxy for "this probably contains substantial real logic" than alphabetical order or directory position — `__init__.py`/stub files are consistently tiny, real implementation files are consistently bigger.
- Capping how many sample files come from any single top-level directory keeps a sample representative of a full-stack repo (both backend and frontend) even when one side happens to have larger files overall.
- A heuristic that "worked" on the first repo tested isn't verified — it needs to be checked against a repo where the *expected* answer is well known (a library famous for heavy typing) so a wrong result is obviously wrong, not just plausible-looking.
- Regex-based code metrics (counting `def ... ->`, `: any`, `interface `) are crude compared to a real parser/AST, but are fast, dependency-free, and good enough for a directional signal fed to an LLM alongside other evidence — not something to over-invest in for a v1.
- `python-dotenv`'s default `load_dotenv()` auto-discovery depends on Python stack introspection (finding the caller's file to search upward from) — this can silently fail in process-spawning setups (like a dev server's auto-reload worker) that don't preserve a normal call stack. Passing an explicit path (built from the calling module's own `__file__`) is more robust than relying on auto-discovery whenever the process might be started in an unusual way.
- A generic frontend error message ("could not reach the backend") can be misleading when the real cause is a backend-side 500 with a non-JSON body (the browser's `.json()` parse then throws, landing in the same catch block as a genuine network failure) — worth remembering that "network error" in the browser can also mean "the server returned something the client couldn't parse," not only "the server is down."
- Never run `cat`/`print` on a file containing secrets to inspect its structure — use tools that show only what's needed (key names, lengths, a parser like `dotenv_values()`) so real secret values never end up in a terminal transcript or conversation log.

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
- Do not add authentication, GitHub analysis, or frontend integration yet. **(Reversed for auth as of the "Sign in with GitHub" feature — see "Current Status"; GitHub analysis and frontend integration were also built long before this note was updated.)**
- Use Python's built-in `sqlite3` module for the first database foundation.
- Store the local SQLite file at `backend/devproof.db`.
- Keep generated SQLite files out of Git.
- Create a minimal `repositories` table before adding repository API endpoints.
- Store only `id`, `url`, and `created_at` for now.
- Do not add analysis fields until the analysis feature needs them.
- Use `?` parameterized SQL queries everywhere, never f-string/string-formatted SQL, to avoid SQL injection.
- Run the local backend on port 8002 (not 8000 or 8001) — 8000 is occupied by local Apache (`httpd`), and 8001 developed an unexplained stuck/orphaned socket on this machine during development. Left both alone rather than digging further; 8002 is now the standard local dev port for the backend.
- Duplicate-URL handling implemented: caught in `main.py` (not `database.py`), keeping `database.py` free of any HTTP/FastAPI knowledge.
- DevProof's real spec is the pitch-competition MVP (username → pick repo → AI report), not just the repository CRUD — see `devproof_pitch_spec` in memory for the full spec. Pitch deadline is days away; prioritize the demo-critical path only, skip polish/hardening not on that path.
- `analysis_report` stored as a single JSON `TEXT` column rather than modeling separate tables for categories/strengths/etc. — simplest option that still lets the whole report round-trip through the API cleanly, given the deadline.
- `POST /repositories/{id}/analyze` always re-fetches fresh GitHub data first (rather than only fetching if never fetched before) — needed to reliably get `default_branch` for the tree call anyway, and keeps stats current for each analysis.
- OpenAI model fixed as a single constant (`OPENAI_MODEL` in `ai_report.py`) rather than configurable — trivial to change later if a better current model is preferred.
- No target-role input field added for the "Role Relevance" scoring category — the model evaluates it generically. Smallest scope that satisfies the spec category given the timeline.

---

# Notes

(Add any personal notes here.)
