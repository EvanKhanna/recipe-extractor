"""Download a TikTok / Instagram Reel and pull out its caption + audio.

Uses yt-dlp (which handles both platforms) plus ffmpeg to extract an mp3 for
transcription. The caller is responsible for removing the returned temp dir.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL


@dataclass
class MediaResult:
    title: str | None
    caption: str
    audio_path: Path | None
    temp_dir: str


def download_audio_and_caption(url: str) -> MediaResult:
    temp_dir = tempfile.mkdtemp(prefix="recipe_")
    outtmpl = str(Path(temp_dir) / "media.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # The description/caption is where written recipes usually live.
    caption = (info.get("description") or "").strip()
    title = info.get("title")

    audio_files = list(Path(temp_dir).glob("media.mp3"))
    audio_path = audio_files[0] if audio_files else None

    return MediaResult(
        title=title,
        caption=caption,
        audio_path=audio_path,
        temp_dir=temp_dir,
    )
