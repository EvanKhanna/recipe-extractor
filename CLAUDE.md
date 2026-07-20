# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this is

**Recipe Extractor** turns an Instagram Reel / TikTok URL **or** a food photo into a
structured recipe (title, ingredients, steps, timings) and saves it to a per-user
cookbook.

- **Frontend:** React 18 + TypeScript (Vite), Clerk auth — `frontend/`
- **Backend:** FastAPI + SQLAlchemy 2.0 on PostgreSQL — `backend/app/`
- **AI extraction:** Claude **Haiku 4.5** via the `anthropic` SDK (vision + text)
- **Audio → text:** faster-whisper, run locally in-container (no extra API key)
- **Media download:** yt-dlp + ffmpeg
- Orchestrated with Docker Compose.

## Run / build

Everything runs in Docker Compose. Copy env first: `cp .env.example .env` and fill in
keys (or set the dev bypass — see below).

```bash
docker compose up --build      # frontend :5173, backend :8000/docs, postgres :5432
```

The Vite dev server proxies `/api` → `backend:8000`, so the browser talks to one
origin (no CORS in dev). The backend mounts source with `--reload`; the frontend runs
`npm run dev`. Both hot-reload on save.

Running services individually (outside Docker):
- Backend: `cd backend && uvicorn app.main:app --reload` (needs a reachable Postgres in `DATABASE_URL`)
- Frontend: `cd frontend && npm install && npm run dev`
- Frontend typecheck/build: `cd frontend && npm run build` (`tsc -b && vite build`)

There is **no test suite or linter configured** yet. Don't invent test commands; if a
change needs verification, exercise the running app.

## Dev auth bypass

To run without a Clerk account, set **both** flags true (they must agree):
- `DISABLE_AUTH=true` — backend accepts unauthenticated requests as fixed `dev-user`
  (`backend/app/auth.py`, `DEV_USER_ID`)
- `VITE_DISABLE_AUTH=true` — frontend skips Clerk entirely (`frontend/src/main.tsx`)

Never enable either in production.

## Request flow (the core of the app)

`backend/app/routers/recipes.py` orchestrates everything:

- **`POST /api/recipes/from-url`** — `media.download_audio_and_caption` (yt-dlp: caption +
  mp3) → `transcribe.transcribe` (faster-whisper, **best-effort**: failures are logged,
  not fatal) → `extractor.extract_from_text` → persist. If there is neither caption nor
  transcript, returns 422. The temp download dir is always cleaned up in a `finally`.
- **`POST /api/recipes/from-image`** — image bytes → base64 → `extractor.extract_from_image`
  (Claude vision) → persist.
- `GET /api/recipes`, `GET /api/recipes/{id}`, `DELETE /api/recipes/{id}` — all scoped to
  the authenticated user; cross-user access returns 404, never 403.

**Abuse controls on the two extraction endpoints** (they cost Claude + Whisper):
`enforce_extraction_quota` (`services/ratelimit.py`) replaces `get_current_user_id` there —
it authenticates *and* applies a per-user rate limit (in-memory, single-instance;
`EXTRACT_RATE_PER_MINUTE`/`_PER_DAY`), returning 429 when exceeded. `from-url` only accepts
`tiktok.com`/`instagram.com` hosts (SSRF guard, validated in `schemas.py`); image uploads
and yt-dlp downloads are size/duration-capped (`MAX_IMAGE_BYTES`, `MAX_VIDEO_BYTES`,
`MAX_VIDEO_DURATION_S`). Reads are not limited. See `docs/DEPLOY.md` §8.

## Conventions & things to know

- **Structured output = forced tool call.** `extractor.py` passes
  `RecipeExtraction.model_json_schema()` as the `save_recipe` tool's `input_schema` and
  sets `tool_choice` to force it. Claude's response must validate against the Pydantic
  model. To change the recipe shape, edit `schemas.py::RecipeExtraction` — the tool
  schema, DB persistence, and API output all derive from it.
- **Model / config** live in `backend/app/config.py` (`pydantic-settings`, env-driven,
  `@lru_cache`d via `get_settings()`). Default model `claude-haiku-4-5`. When touching
  anything Anthropic-related, consult the `claude-api` skill rather than guessing model
  ids / params.
- **DB schema is managed by Alembic migrations** (`backend/alembic/`), applied via
  `alembic upgrade head`, which runs automatically at container startup (see the backend
  `command` in `docker-compose.yml` and the `CMD` in `backend/Dockerfile`). `env.py` reads
  the DB URL from `get_settings()` and targets `Base.metadata`. After changing `models.py`,
  run `alembic revision --autogenerate -m "..."` (against a running DB), review the file,
  then upgrade. A dev volume predating Alembic needs `alembic stamp head` once, or a
  `docker compose down -v` wipe, before `upgrade` will apply cleanly.
- Ingredients and steps are stored as JSON columns on the single `recipes` table
  (`models.py`); there is one table and one model.
- Whisper is warmed in a background thread at startup (`whisper_preload`); the model
  downloads on first use and is cached in the `whisper_models` volume.
- Errors surfaced to clients are deliberately clean HTTP messages; internals are logged
  via the module loggers configured in `main.py`.

## Secrets & git hygiene

- `.env` and `backend/.venv/` are **gitignored and untracked** — keep it that way; never
  `git add -f` them. Only `.env.example` (placeholders) is committed.
- Real Anthropic/Clerk keys live only in the local `.env`. Do not print or commit them.
