# DevProof

**Evidence-based GitHub repository analysis and developer credibility platform.**

DevProof turns a GitHub repository into an objective engineering readiness report. Sign in with GitHub, point it at any public repo (yours or someone else's), and get back an AI-generated assessment grounded in real evidence pulled from the repo itself — not vibes.

## What it does

1. Sign in with your GitHub account.
2. Enter a GitHub username (browse their public repos) or paste a repo URL directly.
3. DevProof fetches the repo's metadata, commit activity, file structure, README, and a sample of its actual source code.
4. That evidence is sent to an LLM with a fixed report schema and returned as a structured report:
   - An overall readiness score
   - Category scores with specific evidence-based comments: Code Organization, Documentation, Testing, DevOps, Security, Collaboration, Project Maturity, Role Relevance, and Code Quality & Type Safety
   - Strengths, weaknesses, concrete recommendations, and a short learning roadmap

## Tech stack

- **Backend:** Python, FastAPI, SQLite
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
```

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

See `docs/COLLABORATOR_GUIDE.md` for a full breakdown of the codebase layout, architecture rules, and contribution workflow. `docs/PROGRESS.md` tracks the full technical history and decisions behind the project.

## License

MIT — see `LICENSE`.
