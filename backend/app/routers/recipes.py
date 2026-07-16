import logging
import shutil

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user_id
from ..database import get_db
from ..models import Recipe
from ..schemas import RecipeCreateFromUrl, RecipeExtraction, RecipeOut
from ..services import extractor, media, transcribe

logger = logging.getLogger("recipes")

router = APIRouter(prefix="/api/recipes", tags=["recipes"])

_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _persist(
    db: Session,
    user_id: str,
    data: RecipeExtraction,
    source_type: str,
    source_url: str | None,
) -> Recipe:
    recipe = Recipe(
        user_id=user_id,
        title=data.title,
        description=data.description,
        ingredients=[i.model_dump() for i in data.ingredients],
        steps=data.steps,
        servings=data.servings,
        prep_time=data.prep_time,
        cook_time=data.cook_time,
        source_type=source_type,
        source_url=source_url,
    )
    db.add(recipe)
    db.commit()
    db.refresh(recipe)
    return recipe


@router.post("/from-url", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
def create_from_url(
    payload: RecipeCreateFromUrl,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Recipe:
    """Download a TikTok / Reel, transcribe it, and extract a recipe."""
    result = None
    try:
        try:
            result = media.download_audio_and_caption(payload.url)
        except Exception as exc:  # noqa: BLE001 — surface a clean error to the client
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not download that video: {exc}",
            ) from exc

        transcript = ""
        if result.audio_path is not None:
            try:
                transcript = transcribe.transcribe(result.audio_path)
            except Exception:  # noqa: BLE001 — transcription is best-effort
                logger.exception("Transcription failed for %s", payload.url)

        # Nothing to work with: no written caption and no speech we could hear.
        if not result.caption and not transcript:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "This post has no caption text and no speech we could transcribe, "
                    "so there was nothing to extract. Try a post that writes out or "
                    "narrates the recipe."
                ),
            )

        try:
            extraction = extractor.extract_from_text(result.caption, transcript)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Recipe extraction failed for %s", payload.url)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not extract a recipe from that post: {exc}",
            ) from exc

        return _persist(db, user_id, extraction, "video", payload.url)
    finally:
        if result is not None:
            shutil.rmtree(result.temp_dir, ignore_errors=True)


@router.post("/from-image", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
def create_from_image(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Recipe:
    """Extract a recipe from an uploaded image."""
    if file.content_type not in _ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image type: {file.content_type}",
        )

    image_bytes = file.file.read()
    try:
        extraction = extractor.extract_from_image(image_bytes, file.content_type)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Recipe extraction from image failed")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not extract a recipe from that image: {exc}",
        ) from exc

    return _persist(db, user_id, extraction, "image", None)


@router.get("", response_model=list[RecipeOut])
def list_recipes(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[Recipe]:
    stmt = select(Recipe).where(Recipe.user_id == user_id).order_by(Recipe.created_at.desc())
    return list(db.scalars(stmt).all())


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(
    recipe_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Recipe:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    return recipe


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_recipe(
    recipe_id: int,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    recipe = db.get(Recipe, recipe_id)
    if recipe is None or recipe.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")
    db.delete(recipe)
    db.commit()
