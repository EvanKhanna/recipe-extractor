"""Download a TikTok / Instagram Reel and pull out its caption + audio.

Uses yt-dlp (which handles both platforms) plus ffmpeg to extract an mp3 for
transcription. The caller is responsible for removing the returned temp dir.
"""

import tempfile
from dataclasses import dataclass
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import match_filter_func

from ..config import get_settings


@dataclass
class MediaResult:
    title: str | None
    caption: str
    audio_path: Path | None
    temp_dir: str


def download_audio_and_caption(url: str) -> MediaResult:
    settings = get_settings()
    temp_dir = tempfile.mkdtemp(prefix="recipe_")
    outtmpl = str(Path(temp_dir) / "media.%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "noplaylist": True,
        # Abuse/cost guards: abort large downloads, reject over-long videos, and
        # don't hang forever on a slow host.
        "max_filesize": settings.max_video_bytes,
        "match_filter": match_filter_func([f"duration <? {settings.max_video_duration_s}"]),
        "socket_timeout": 30,
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
