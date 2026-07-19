# Backend — Recipe Extractor API

FastAPI service that downloads social-media cooking videos (or accepts an image),
transcribes speech locally with faster-whisper, and extracts a structured recipe with
Claude Haiku 4.5. See the root [`README.md`](../README.md) for the full project overview
and [`CLAUDE.md`](../CLAUDE.md) for a working map of the codebase.

## Layout

```
backend/
├── Dockerfile
├── requirements.txt
├── alembic.ini           # Alembic config (DB url injected from settings at runtime)
├── alembic/              # Migrations: env.py + versions/ (schema history)
└── app/
    ├── main.py            # FastAPI app, CORS, startup (Whisper preload)
    ├── config.py          # Settings (pydantic-settings, env-driven, cached)
    ├── database.py        # SQLAlchemy engine, session, Base, get_db dependency
    ├── models.py          # Recipe ORM model (single table)
    ├── schemas.py         # Pydantic models incl. RecipeExtraction (the AI output shape)
    ├── auth.py            # Clerk JWT verification / DISABLE_AUTH dev bypass
    ├── routers/
    │   └── recipes.py     # All HTTP endpoints
    └── services/
        ├── media.py       # yt-dlp + ffmpeg: download audio + caption
        ├── transcribe.py  # faster-whisper speech-to-text
        └── extractor.py   # Claude Haiku 4.5 structured extraction (forced tool call)
```

## Running

### With Docker (recommended)
From the repo root: `docker compose up --build`. The backend serves on
<http://localhost:8000> with interactive docs at <http://localhost:8000/docs>.

### Standalone (local Python)
Requires a reachable PostgreSQL and `ffmpeg` on the PATH.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Point DATABASE_URL at your Postgres (or run just the db service via compose)
export DATABASE_URL="postgresql+psycopg://recipes:recipes@localhost:5432/recipes"
export DISABLE_AUTH=true          # skip Clerk for local dev
export ANTHROPIC_API_KEY=sk-ant-...
alembic upgrade head              # create/upgrade the schema before first run
uvicorn app.main:app --reload
```

Under Docker this migration step runs automatically as part of the backend start
command; standalone you run it yourself (as above).

Config is read from environment variables (and a `.env` file, via `pydantic-settings`).
See [`.env.example`](../.env.example) for every variable.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET`    | `/api/health`            | Liveness check |
| `POST`   | `/api/recipes/from-url`  | Extract a recipe from a TikTok / Reel URL |
| `POST`   | `/api/recipes/from-image`| Extract a recipe from an uploaded image (multipart `file`) |
| `GET`    | `/api/recipes`           | List the current user's recipes |
| `GET`    | `/api/recipes/{id}`      | Fetch one recipe (owner only) |
| `DELETE` | `/api/recipes/{id}`      | Delete one recipe (owner only) |

All `/api/recipes` routes require a Clerk bearer token unless `DISABLE_AUTH=true`, in
which case every request runs as the fixed `dev-user`. Recipes are always scoped to the
authenticated user; accessing someone else's recipe returns 404.

## Notes & gotchas

- **Structured output** is a forced `save_recipe` tool call whose `input_schema` is
  `RecipeExtraction.model_json_schema()`. To change the recipe shape, edit
  `schemas.py::RecipeExtraction` — the tool schema, DB write, and API response all derive
  from it.
- **Migrations (Alembic).** The schema is managed by migrations in `alembic/versions/`,
  applied via `alembic upgrade head` (run automatically at container startup). After
  changing `models.py`, generate a migration with
  `alembic revision --autogenerate -m "describe change"` (needs a running DB to diff
  against), review the generated file, then upgrade. `alembic/env.py` reads the DB URL
  from app settings and points at `Base.metadata`.
  - **Existing dev volume from before Alembic?** It has the `recipes` table but no
    `alembic_version` row, so `upgrade` will collide. Either wipe it
    (`docker compose down -v`) or run `alembic stamp head` once to mark it as already
    at the initial revision.
- **Transcription is best-effort.** If faster-whisper fails, it's logged and extraction
  proceeds on the caption alone; a post with neither caption nor transcript returns 422.
- **First video is slow** — the Whisper model downloads on first use (cached in the
  `whisper_models` volume). It's also warmed in a background thread at startup.
- **No tests or linter** are configured yet.
