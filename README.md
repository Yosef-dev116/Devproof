# DevProof

**Evidence-based GitHub repository analysis and developer credibility platform.**

**Live:** [devproof-xi.vercel.app](https://devproof-xi.vercel.app) — sign in with GitHub and try it.

DevProof turns GitHub activity into an objective, evidence-based report — for two different audiences:

1. **Individual candidate reports** (recruiters/job seekers): point it at any public repo and get an AI-generated engineering readiness report grounded in real evidence, not vibes. Also includes a "Verify a Resume Against GitHub" check that cross-references resume claims against real GitHub activity.
2. **Team/org analysis** (engineering managers, new as of 2026-07-30): point it at a whole GitHub organization and get an honest picture of the team's contribution patterns and code quality — not just commit counts, actual code analysis, aggregated across every repo in the org.

## What it does

**Individual repo analysis:**
1. Sign in with your GitHub account.
2. Enter a GitHub username (browse their public repos) or paste a repo URL directly.
3. DevProof fetches the repo's metadata, commit activity, file structure, README, and a sample of its actual source code.
4. That evidence is sent to an LLM with a fixed report schema and returned as a structured report:
   - An overall readiness score
   - Category scores with specific evidence-based comments: Code Organization, Documentation, Testing, DevOps, Security, Collaboration, Project Maturity, Role Relevance, and Code Quality & Type Safety
   - Strengths, weaknesses, concrete recommendations, and a short learning roadmap

**Team/org analysis** (backend only so far, no frontend UI yet):
- `GET /organizations/{org_name}/contributors` — fetches every repository in a GitHub org and returns contributors aggregated with their total commit counts across the whole org (forks and bot accounts excluded so the numbers reflect the org's own human contributors).
- `GET /organizations/{org_name}/engineering-report` — goes beyond commit counts: for the org's top 10 contributors by commits, reuses the existing single-repo AI analysis pipeline on the repos they meaningfully contributed to (≥5 commits, deduplicated across contributors, capped at ~15 unique repos per request to bound cost/latency) and aggregates each contributor's own documentation/testing/DevOps/security/project-maturity/code-quality scores, an overall engineering score, evidence-based strengths/weaknesses, rule-based risk flags, and a summary. Never invents a score - a contributor with no analyzed repos in a given run gets explicit `null` scores and a note, not a fabricated number.

## Tech stack

- **Backend:** Python, FastAPI, Postgres
- **Frontend:** React, TypeScript, Vite
- **AI:** OpenAI API (`gpt-4o-mini`, JSON mode)
- **Auth:** "Sign in with GitHub" (OAuth), cookie-based sessions

## Local setup

```powershell
# Backend
cd backend
pip install -r requirements.txt
```

Create `backend/.env` (see `backend/.env.example` for the full list):

```
OPENAI_API_KEY=your-openai-api-key-here
GITHUB_TOKEN=your-github-personal-access-token-here
GITHUB_OAUTH_CLIENT_ID=your-github-oauth-client-id-here
GITHUB_OAUTH_CLIENT_SECRET=your-github-oauth-client-secret-here
DATABASE_URL=postgresql://user:password@host:5432/devproof
```

`DATABASE_URL` must point at a real Postgres database (a local install, or a free hosted one) - SQLite is no longer used.

Run the backend from the repo root:

```powershell
uvicorn backend.app.main:app --reload --port 8002
```

```powershell
# Frontend
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5180`.

## Running tests

```powershell
python -m pytest backend/tests -v
```

## Project structure

See `docs/COLLABORATOR_GUIDE.md` for a full breakdown of the codebase layout, architecture rules, and contribution workflow. `docs/PROGRESS.md` tracks the full technical history and decisions behind the project. `docs/DEPLOYMENT.md` covers deploying a public, phone-accessible instance (Render + Vercel).

## License

MIT — see `LICENSE`.
