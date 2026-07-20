# Deploying Recipe Extractor (Render + Neon)

This is the runbook to take the app from local-only to hosted for a small group.
Architecture:

```
 Browser / iOS  ──►  recipe-extractor-web   (Render static site: the Vite build)
                        │  calls VITE_API_URL
                        ▼
                     recipe-extractor-api   (Render web service: FastAPI in Docker)
                        │  DATABASE_URL
                        ▼
                     Neon PostgreSQL         (free, external managed database)
```

Everything for the two Render services is declared in [`render.yaml`](../render.yaml)
(a Render *Blueprint*). You provide the database and the secrets.

---

## 0. Prerequisites

- A **Render** account (you have this).
- A **Neon** account — <https://neon.tech> (free).
- Your **Anthropic API key** (`sk-ant-...`).
- **Clerk** keys. You can start with your existing dev keys (`pk_test_`/`sk_test_`) to
  validate the deployment, then create a Clerk **Production** instance for real use.
- The `render.yaml` must be on the branch Render will track. **Merge this branch to
  `main` first** (via the PR), then point Render at `main`.

---

## 1. Create the database (Neon)

1. In the Neon console, create a project (e.g. `recipe-extractor`). It creates a
   database and a default branch for you.
2. Copy the **connection string**. It looks like:
   ```
   postgresql://USER:PASSWORD@ep-xxxx.us-east-2.aws.neon.tech/dbname?sslmode=require
   ```
3. **Rewrite the scheme** from `postgresql://` to `postgresql+psycopg://` so SQLAlchemy
   uses this app's psycopg (v3) driver. Keep `?sslmode=require`. Final form:
   ```
   postgresql+psycopg://USER:PASSWORD@ep-xxxx.us-east-2.aws.neon.tech/dbname?sslmode=require
   ```
   Save this — it's the `DATABASE_URL` secret in step 3.

> You do **not** need to create any tables. On first deploy the backend runs
> `alembic upgrade head` automatically and creates the `recipes` table. A fresh Neon
> DB has no pre-Alembic table, so there's no "relation already exists" collision.

---

## 2. (Optional now, required for real use) Clerk production instance

Dev keys work for a first smoke test but show a development banner and have low limits.
For real use:

1. In the Clerk dashboard, create/point a **Production** instance.
2. Grab the **Publishable key** (`pk_live_...`), **Secret key** (`sk_live_...`), and your
   **Frontend API / issuer URL** (e.g. `https://your-app.clerk.accounts.dev`, or your
   custom domain). These map to `VITE_CLERK_PUBLISHABLE_KEY`, `CLERK_SECRET_KEY`, and
   `CLERK_JWT_ISSUER`.
3. Add the frontend's URL (`https://recipe-extractor-web.onrender.com`) to Clerk's list
   of allowed origins / domains.

---

## 3. Deploy the Blueprint (Render)

1. Render Dashboard → **New** → **Blueprint**.
2. Connect the GitHub repo and select the **`main`** branch. Render reads `render.yaml`
   and shows two services: `recipe-extractor-api` and `recipe-extractor-web`.
3. Render will prompt for every `sync: false` env var. Fill them in:

   **recipe-extractor-api**
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the `postgresql+psycopg://...` Neon URL from step 1 |
   | `ANTHROPIC_API_KEY` | `sk-ant-...` |
   | `CLERK_SECRET_KEY` | `sk_test_...` or `sk_live_...` |
   | `CLERK_JWT_ISSUER` | `https://your-app.clerk.accounts.dev` |

   **recipe-extractor-web**
   | Key | Value |
   |---|---|
   | `VITE_CLERK_PUBLISHABLE_KEY` | `pk_test_...` or `pk_live_...` |

4. **Apply**. Render provisions the disk, builds the Docker image, runs
   `alembic upgrade head`, and starts uvicorn. First deploy is slower because the
   Whisper `small` model downloads into the persistent disk (subsequent deploys reuse it).

> **If Render appended a suffix to a service name** (because the name was taken), the two
> cross-referencing URLs in `render.yaml` are now wrong. Update `CORS_ORIGINS` (api) and
> `VITE_API_URL` (web) to the real URLs, commit, and let it redeploy.

---

## 4. Verify

1. **Backend health:** open `https://recipe-extractor-api.onrender.com/api/health` →
   `{"status":"ok"}`. Also check `/docs`.
2. **DB migration ran:** in Render's api-service logs you should see Alembic apply
   revision `0001`. In Neon, the `recipes` and `alembic_version` tables now exist.
3. **Frontend:** open `https://recipe-extractor-web.onrender.com`, sign in via Clerk,
   and load the app.
4. **End-to-end image path:** add a recipe from a food photo (this exercises Claude
   vision + DB write without touching yt-dlp).

---

## 5. ⚠️ The yt-dlp test (the known risk)

Downloading from Instagram/TikTok works from a home IP but is frequently **rate-limited
or blocked from datacenter IPs** like Render's. Test this deliberately and early:

1. Add a recipe **from a URL** (a public Reel/TikTok).
2. Watch the api-service logs.
   - **Works** → great, nothing to do.
   - **Fails** with HTTP 403/429, "Sign in to confirm", or "Unable to extract" → it's the
     datacenter-IP block, not a bug in our code.

Mitigations if it's blocked (in rough order of effort):
- Keep `yt-dlp` updated (extractors change often); it's pinned in `requirements.txt`.
- Supply cookies from a logged-in session via a yt-dlp cookies file/env.
- Route yt-dlp through a **residential proxy**.
- Fall back to the **image path** for problem sources.

We'll tackle this hands-on once we see how Render's IPs are treated.

---

## 6. Ongoing operations

- **Deploys:** `autoDeploy: true` — every push to `main` rebuilds and redeploys. Migrations
  run automatically on each start (`alembic upgrade head` is idempotent — no-op when there's
  nothing pending).
- **Schema changes:** edit `models.py` → `alembic revision --autogenerate -m "..."` against a
  running DB → review → commit. The next deploy applies it.
- **Rollback:** Render keeps prior deploys; roll back from the dashboard. (Note: a rollback
  does not auto-revert a migration — write a down-migration if a schema change must be undone.)
- **Secrets rotation:** update the env var in the Render dashboard; it triggers a redeploy.

---

## 7. Cost summary (approx.)

| Piece | Plan | Cost |
|---|---|---|
| Backend (`recipe-extractor-api`) | Render Standard, 2 GB | ~$25/mo |
| Persistent disk (Whisper cache) | 2 GB | ~$0.50/mo |
| Frontend (`recipe-extractor-web`) | Render static site | Free |
| Database | Neon free tier | Free |
| Clerk | Free tier | Free |

The backend instance is the main cost; it's sized for the local Whisper `small` model. If
you later move transcription to an API or a smaller model, you can drop to a cheaper plan.

---

## 8. Security & abuse controls

The app has real auth (Clerk JWTs) and per-user data isolation. The additional controls
below exist because every extraction costs money (Claude) and CPU (Whisper), and because
the URL endpoint drives a downloader.

- **Restrict who can sign up (do this).** By default anyone who finds the URL can create a
  Clerk account and spend your Claude credits. Lock it down in the **Clerk dashboard**:
  - **Restrictions** → enable an **allowlist** and add only your friends' emails (or turn on
    "Restrict sign-ups" / invite-only), so strangers can't self-register.
  - This is the single most important control for a small private app.
- **Per-user rate limits** (env-driven, enforced in-memory): `EXTRACT_RATE_PER_MINUTE`
  (default 5) and `EXTRACT_RATE_PER_DAY` (default 50) cap the extraction endpoints per user.
  Over the limit returns HTTP 429 with `Retry-After`. Reads are not limited. Note: counters
  are in-memory and reset on restart — fine for a single instance; move to Redis if you ever
  scale out.
- **SSRF guard:** `/from-url` only accepts `tiktok.com` / `instagram.com` hosts (and
  subdomains); anything else is a 422 before the downloader runs.
- **Size / duration caps:** `MAX_IMAGE_BYTES` (10 MB), `MAX_VIDEO_BYTES` (80 MB), and
  `MAX_VIDEO_DURATION_S` (30 min) bound memory, bandwidth, and Whisper cost.
- **Keep `DISABLE_AUTH=false`** in production (it is). Setting it true bypasses auth entirely.
- **Keep `yt-dlp` / `ffmpeg` updated** — they process untrusted media; update the pins
  periodically.
