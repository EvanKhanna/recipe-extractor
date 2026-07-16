# 🍳 Recipe Extractor

Turn an **Instagram Reel**, **TikTok**, or **food image** into a structured recipe —
ingredient list + step-by-step instructions — and save it to your personal cookbook.

- **Frontend:** React + TypeScript (Vite)
- **Backend:** FastAPI (Python)
- **Database:** PostgreSQL
- **Auth:** [Clerk](https://clerk.com)
- **AI extraction:** Claude **Haiku 4.5** (Anthropic) — cheap + capable, with vision
- **Audio → text:** [faster-whisper](https://github.com/SYSTRAN/faster-whisper), running locally in-container (no extra API key)
- **Media download:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) + ffmpeg
- **Everything runs in Docker Compose.**

## How it works

```
        ┌────────────┐     URL or image      ┌─────────────┐
        │  React UI  │ ───────────────────▶  │  FastAPI    │
        │  (Clerk)   │ ◀── saved recipe ────  │  backend    │
        └────────────┘                        └──────┬──────┘
                                                      │
                 ┌────────────────────────────────────┼───────────────────────┐
                 ▼                    ▼                ▼                        ▼
           yt-dlp + ffmpeg     faster-whisper    Claude Haiku 4.5         PostgreSQL
           (download video,    (spoken audio     (transcript+caption      (store recipe
            grab caption)       → transcript)      or image → recipe)       per user)
```

1. You paste a TikTok/Reel URL **or** upload a photo of a recipe.
2. For a video: the backend downloads it, pulls the caption/description, extracts the
   audio, and transcribes any spoken instructions with faster-whisper.
3. The combined text (or the image) is sent to **Claude Haiku 4.5**, which returns a
   structured recipe (title, ingredients, steps, timings).
4. The recipe is saved to Postgres, scoped to your Clerk user, and shown in your cookbook.

## Quick start

### 1. Prerequisites
- Docker + Docker Compose
- A [Clerk](https://dashboard.clerk.com) application (free) — grab the **Publishable key**, **Secret key**, and your **Frontend API / Issuer URL**.
- An [Anthropic API key](https://console.anthropic.com).

### 2. Configure
```bash
cp .env.example .env
# then edit .env and fill in your Clerk + Anthropic keys
```

### 3. Run
```bash
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend API + docs: http://localhost:8000/docs

The first video you process will download the Whisper model (cached in a Docker
volume afterward), so give it a minute.

## Environment variables

See [`.env.example`](.env.example). The essentials:

| Variable | Where | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | backend | Claude API key |
| `CLERK_SECRET_KEY` | backend | Verify Clerk sessions server-side |
| `CLERK_JWT_ISSUER` | backend | Clerk issuer URL, e.g. `https://your-app.clerk.accounts.dev` |
| `VITE_CLERK_PUBLISHABLE_KEY` | frontend | Clerk publishable key |
| `WHISPER_MODEL` | backend | faster-whisper model size (`tiny`/`base`/`small`/`medium`) |
| `DISABLE_AUTH` | backend | Dev-only: set `true` to bypass Clerk (uses a fixed dev user) |

## Local development without Docker

See [`backend/README`](backend/) notes in the code; you can also run each service
directly (`uvicorn` for the backend, `npm run dev` for the frontend) if you prefer.

## Project layout
```
recipe-extractor/
├── docker-compose.yml
├── backend/          # FastAPI app
│   └── app/
│       ├── routers/  # HTTP endpoints
│       └── services/ # media download, transcription, Claude extraction
└── frontend/         # React + Vite app
    └── src/
```

## License
MIT
