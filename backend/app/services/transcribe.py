"""Transcribe spoken audio to text with faster-whisper (runs locally, no API key)."""

from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel

from ..config import get_settings


@lru_cache
def _model() -> WhisperModel:
    settings = get_settings()
    # int8 on CPU keeps memory + CPU reasonable while staying accurate enough.
    return WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")


def transcribe(audio_path: Path) -> str:
    segments, _info = _model().transcribe(str(audio_path))
    return " ".join(segment.text.strip() for segment in segments).strip()
