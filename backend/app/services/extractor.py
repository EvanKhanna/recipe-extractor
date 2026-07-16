"""Turn raw recipe material (transcript + caption, or an image) into a structured
recipe using Claude Haiku 4.5.

We use a forced tool call as the structured-output mechanism: the tool's input
schema *is* the recipe schema, so Claude must return data that validates against
it. This is robust across Anthropic SDK versions and works on Haiku 4.5.
"""

import base64

from anthropic import Anthropic

from ..config import get_settings
from ..schemas import RecipeExtraction

_SYSTEM = (
    "You extract structured cooking recipes from social-media content. "
    "Given a transcript of a cooking video, its caption, and/or an image, "
    "produce a clean, complete recipe. Infer reasonable quantities and steps "
    "when they are implied but not stated explicitly. If something is genuinely "
    "unknown, leave that field null rather than guessing wildly. Always return "
    "the recipe via the `save_recipe` tool."
)

_TOOL = {
    "name": "save_recipe",
    "description": "Save the structured recipe extracted from the content.",
    "input_schema": RecipeExtraction.model_json_schema(),
}


def _client() -> Anthropic:
    settings = get_settings()
    return Anthropic(api_key=settings.anthropic_api_key)


def _extract(content_blocks: list[dict]) -> RecipeExtraction:
    settings = get_settings()
    response = _client().messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=_SYSTEM,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "save_recipe"},
        messages=[{"role": "user", "content": content_blocks}],
    )

    for block in response.content:
        if block.type == "tool_use" and block.name == "save_recipe":
            return RecipeExtraction.model_validate(block.input)

    raise ValueError("Claude did not return a structured recipe.")


def extract_from_text(caption: str, transcript: str) -> RecipeExtraction:
    parts = []
    if caption:
        parts.append(f"CAPTION / DESCRIPTION:\n{caption}")
    if transcript:
        parts.append(f"SPOKEN TRANSCRIPT:\n{transcript}")
    if not parts:
        raise ValueError("No caption or transcript was available to extract from.")

    text = (
        "Extract the recipe from the following social-media cooking post.\n\n"
        + "\n\n".join(parts)
    )
    return _extract([{"type": "text", "text": text}])


def extract_from_image(image_bytes: bytes, media_type: str) -> RecipeExtraction:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    return _extract(
        [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": b64},
            },
            {
                "type": "text",
                "text": "Extract the full recipe shown in this image.",
            },
        ]
    )
