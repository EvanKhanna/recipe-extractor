from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Only these hosts (and their subdomains) may be handed to yt-dlp. This is the
# primary defense against SSRF: without it, an authenticated user could point the
# downloader at internal addresses (localhost, cloud metadata, internal services).
_ALLOWED_URL_HOSTS = ("instagram.com", "tiktok.com")


class Ingredient(BaseModel):
    quantity: str | None = Field(
        default=None, description="Amount, e.g. '2 cups' or '1 tbsp'. Null if unspecified."
    )
    item: str = Field(description="The ingredient name, e.g. 'all-purpose flour'.")


class RecipeExtraction(BaseModel):
    """The structured recipe Claude is asked to produce."""

    title: str = Field(description="A short, descriptive name for the dish.")
    description: str | None = Field(
        default=None, description="One or two sentences describing the dish."
    )
    ingredients: list[Ingredient] = Field(
        default_factory=list, description="Every ingredient with its quantity."
    )
    steps: list[str] = Field(
        default_factory=list,
        description="Ordered preparation steps, each a full sentence.",
    )
    servings: str | None = Field(default=None, description="e.g. '4 servings'. Null if unknown.")
    prep_time: str | None = Field(default=None, description="e.g. '15 minutes'. Null if unknown.")
    cook_time: str | None = Field(default=None, description="e.g. '30 minutes'. Null if unknown.")


class RecipeCreateFromUrl(BaseModel):
    url: str = Field(description="A TikTok or Instagram Reel URL.")

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        parsed = urlparse(v.strip())
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must start with http:// or https://")
        host = (parsed.hostname or "").lower()
        # Accept the allowed domains and any of their subdomains (e.g. www.,
        # vm.tiktok.com), but nothing else.
        if not any(host == d or host.endswith("." + d) for d in _ALLOWED_URL_HOSTS):
            raise ValueError("Only TikTok and Instagram URLs are supported.")
        return v.strip()


class RecipeOut(BaseModel):
    id: int
    title: str
    description: str | None
    ingredients: list[Ingredient]
    steps: list[str]
    servings: str | None
    prep_time: str | None
    cook_time: str | None
    source_type: str
    source_url: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
