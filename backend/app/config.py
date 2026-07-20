from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://recipes:recipes@db:5432/recipes"

    # Anthropic / Claude
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-haiku-4-5"

    # Clerk
    clerk_secret_key: str = ""
    clerk_jwt_issuer: str = ""

    # Transcription
    whisper_model: str = "small"
    # Warm the Whisper model at startup (background thread) for a reliable first request.
    whisper_preload: bool = True

    # Dev toggles
    disable_auth: bool = False
    cors_origins: str = "http://localhost:5173"

    # ---- Abuse / cost controls (per authenticated user) ----
    # The extraction endpoints each cost real money (Claude) + CPU (Whisper), so
    # they are rate-limited per user. Reads are not limited.
    extract_rate_per_minute: int = 5
    extract_rate_per_day: int = 50

    # ---- Upload / download size limits (bytes / seconds) ----
    max_image_bytes: int = 10 * 1024 * 1024  # 10 MB uploaded image
    max_video_bytes: int = 80 * 1024 * 1024  # 80 MB downloaded media
    max_video_duration_s: int = 1800  # 30 min — bounds Whisper cost

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
