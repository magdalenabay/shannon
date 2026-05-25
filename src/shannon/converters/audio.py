from __future__ import annotations

from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


AUDIO_FORMATS = ("mp3", "wav", "flac", "ogg", "m4a", "opus", "aac", "wma", "aiff")


def ffmpeg_audio_codec(out_fmt: str, opts: Opts) -> list[str]:
    if out_fmt == "mp3":
        q = {"low": "7", "medium": "4", "high": "0"}[opts.quality]
        return ["-c:a", "libmp3lame", "-q:a", q]
    if out_fmt == "ogg":
        q = {"low": "3", "medium": "5", "high": "8"}[opts.quality]
        return ["-c:a", "libvorbis", "-q:a", q]
    if out_fmt == "opus":
        kbps = {"low": "64", "medium": "128", "high": "192"}[opts.quality]
        return ["-c:a", "libopus", "-b:a", f"{kbps}k"]
    if out_fmt in ("m4a", "aac"):
        kbps = {"low": "96", "medium": "192", "high": "256"}[opts.quality]
        return ["-c:a", "aac", "-b:a", f"{kbps}k"]
    if out_fmt == "flac":
        return ["-c:a", "flac"]
    if out_fmt == "wav":
        return ["-c:a", "pcm_s16le"]
    if out_fmt == "aiff":
        return ["-c:a", "pcm_s16be"]
    if out_fmt == "wma":
        return ["-c:a", "wmav2"]
    return []


@register(
    inputs=AUDIO_FORMATS,
    outputs=AUDIO_FORMATS,
    requires=("ffmpeg",),
    category="audio",
    priority=10,
)
def audio_to_audio(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if opts.start:
        cmd += ["-ss", opts.start]
    cmd += ["-i", str(src)]
    if opts.duration:
        cmd += ["-t", opts.duration]
    cmd += ffmpeg_audio_codec(out_fmt, opts) + ["-vn", str(dst)]
    run(cmd, verbose=opts.verbose)
