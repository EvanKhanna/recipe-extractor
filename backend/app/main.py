import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import recipes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("app")

settings = get_settings()


def _preload_whisper() -> None:
    """Warm the Whisper model in the background so the first video that needs
    transcription doesn't pay the (potentially large) model-download cost inline."""
    try:
        from .services.transcribe import get_model

        get_model()
        logger.info("Whisper model '%s' is ready.", settings.whisper_model)
    except Exception:  # noqa: BLE001 — preloading is best-effort
        logger.exception("Whisper model preload failed (will retry lazily on first use).")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic migrations (`alembic upgrade head`), run as a
    # startup step in the container command — not here. See docker-compose.yml /
    # Dockerfile and backend/alembic/.
    if settings.whisper_preload:
        threading.Thread(target=_preload_whisper, daemon=True).start()
    yield


app = FastAPI(title="Recipe Extractor API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(recipes.router)
