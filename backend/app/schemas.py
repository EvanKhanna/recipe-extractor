from datetime import datetime

from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True
