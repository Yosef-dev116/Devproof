# Deploying DevProof publicly (Render + Vercel)

Goal: a real public link, working from a phone, where anyone can sign in with
their own GitHub account and analyze any public repo. This is the path used
for that: **Render** hosts the FastAPI backend + a Postgres database,
**Vercel** hosts the React frontend.

This is a one-time setup. Steps that need your own accounts/clicks are marked
**(you do this)** — the code side is already done in this repo.

---

## 0. Before you start

- Push all current changes to `main` (or your deploy branch) on GitHub first — both Render and Vercel deploy by connecting to your GitHub repo.
- Have your `OPENAI_API_KEY` and a `GITHUB_TOKEN` (personal access token, no special scopes) ready — same ones from local dev.

---

## 1. Backend + database on Render **(you do this)**

1. Go to `render.com` and sign in (GitHub sign-in is easiest — same account, one less password).
2. **New > Blueprint** → connect your DevProof GitHub repo. Render will read `render.yaml` at the repo root and propose:
   - A free Postgres database (`devproof-db`)
   - A web service (`devproof-api`) built from the repo's `Dockerfile`
3. Render will prompt you to fill in the env vars marked `sync: false` in `render.yaml`. Enter:
   - `OPENAI_API_KEY` — your real key
   - `GITHUB_TOKEN` — your real token
   - `GITHUB_OAUTH_CLIENT_ID` / `GITHUB_OAUTH_CLIENT_SECRET` — **leave blank for now**, you'll create this in step 3 below and come back to fill these in
   - `BACKEND_URL` — leave blank for now too; Render assigns the service a URL like `https://devproof-api.onrender.com` only after the first deploy. Come back and set this once you know it (then trigger a manual redeploy so the OAuth code picks it up).
   - `FRONTEND_URL` / `FRONTEND_ORIGINS` — leave blank for now; you'll fill these in after step 2 gives you the Vercel URL.
4. Click **Apply** / **Create**. Render provisions the database and deploys the web service. `DATABASE_URL` is wired automatically (Render injects the Postgres connection string).
5. Once deployed, note the backend's public URL (e.g. `https://devproof-api.onrender.com`) — you'll need it in the next steps.

**Free-tier note:** Render's free web services spin down after inactivity and take ~30-60s to wake back up on the next request. For a live pitch demo, either upgrade to a paid instance for the day, or "warm it up" by loading the site a minute or two before you go on stage.

---

## 2. Frontend on Vercel **(you do this)**

1. Go to `vercel.com`, sign in with GitHub, **Add New > Project**, select the DevProof repo.
2. Set the project's **Root Directory** to `frontend`.
3. Framework preset: Vite (Vercel usually auto-detects this).
4. Add an environment variable:
   - `VITE_API_BASE_URL` = the Render backend URL from step 1 (e.g. `https://devproof-api.onrender.com`)
5. Deploy. Vercel gives you a URL like `https://devproof.vercel.app` (or a project-specific subdomain).

---

## 3. A new GitHub OAuth App for production **(you do this)**

Your existing local-dev OAuth App (callback `http://localhost:8002/...`) can only redirect to one URL. Rather than repointing it and breaking local dev, create a **second** OAuth App for production:

1. `github.com/settings/developers` → **OAuth Apps** → **New OAuth App**.
2. **Homepage URL:** your Vercel URL (e.g. `https://devproof.vercel.app`)
3. **Authorization callback URL:** your Render backend URL + `/auth/github/callback` (e.g. `https://devproof-api.onrender.com/auth/github/callback`)
4. Create it, then generate a **Client Secret**.
5. Copy the new **Client ID** and **Client Secret**.

---

## 4. Wire the URLs together

Now that you have both real URLs and the new OAuth app credentials, go back to Render's dashboard for `devproof-api` → **Environment**, and set:

- `GITHUB_OAUTH_CLIENT_ID` = the new prod OAuth app's client ID
- `GITHUB_OAUTH_CLIENT_SECRET` = the new prod OAuth app's client secret
- `BACKEND_URL` = `https://devproof-api.onrender.com` (your actual Render URL)
- `FRONTEND_URL` = `https://devproof.vercel.app` (your actual Vercel URL)
- `FRONTEND_ORIGINS` = same as `FRONTEND_URL` (comma-separate if you also use a custom domain later)

Save — Render redeploys automatically when env vars change.

---

## 5. Verify it actually works end-to-end

From a phone (not just your laptop, to catch anything mobile-specific):

1. Open the Vercel URL.
2. Click "Sign in with GitHub" — confirm it redirects to GitHub, back to the app, and shows you as logged in.
3. Type any GitHub username, pick a repo, confirm a real report generates.
4. Try the resume-check feature.
5. Log out, confirm you're logged out cleanly.

If login redirects successfully but the app still acts logged-out: double check `BACKEND_URL`/`FRONTEND_URL` are the exact real URLs (no trailing slash mismatches) and that `ENVIRONMENT=production` is set on Render — the session cookie's `SameSite=None; Secure` flags (required for a cross-domain cookie between vercel.app and onrender.com) are only enabled when that's set.

---

## Notes / limitations of this setup

- **Rate limiting is in-memory**, per backend process (`backend/app/rate_limit.py`, capped at 20 analyses/hour and 20 resume-checks/hour per logged-in user). It resets on every deploy/restart and only works correctly with a single backend instance — fine for a free-tier Render service (which runs one instance), but wouldn't hold up if you later scale to multiple instances without moving this to the database.
- **Anyone with the link can use it** with their own OpenAI/GitHub-API cost hitting your keys — the rate limit caps runaway usage per user, but there's no cap on total signups. Fine for a pitch/demo; revisit before any real public launch.
- **Free-tier cold starts** (Render backend, possibly Postgres too) mean the first request after idle time is slow — see the warm-up note in step 1.
