from __future__ import annotations

from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts
from .audio import AUDIO_FORMATS, ffmpeg_audio_codec


VIDEO_FORMATS = ("mp4", "webm", "mkv", "mov", "avi", "wmv", "flv")


def _video_codec(out_fmt: str, opts: Opts) -> list[str]:
    if out_fmt == "webm":
        crf = {"low": "40", "medium": "32", "high": "24"}[opts.quality]
        return [
            "-c:v",
            "libvpx-vp9",
            "-crf",
            crf,
            "-b:v",
            "0",
            "-row-mt",
            "1",
            "-c:a",
            "libopus",
        ]
    if out_fmt == "mp4":
        crf = {"low": "30", "medium": "23", "high": "18"}[opts.quality]
        preset = "veryfast" if opts.fast else "medium"
        return [
            "-c:v",
            "libx264",
            "-crf",
            crf,
            "-preset",
            preset,
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
        ]
    if out_fmt == "mkv":
        crf = {"low": "30", "medium": "23", "high": "18"}[opts.quality]
        return ["-c:v", "libx264", "-crf", crf, "-c:a", "aac"]
    if out_fmt == "mov":
        return ["-c:v", "libx264", "-c:a", "aac"]
    if out_fmt == "avi":
        return ["-c:v", "mpeg4", "-q:v", "5", "-c:a", "libmp3lame"]
    if out_fmt == "wmv":
        return ["-c:v", "wmv2", "-c:a", "wmav2"]
    if out_fmt == "flv":
        return ["-c:v", "flv", "-c:a", "libmp3lame"]
    return []


@register(
    inputs=VIDEO_FORMATS,
    outputs=VIDEO_FORMATS,
    requires=("ffmpeg",),
    category="video",
    priority=10,
)
def video_to_video(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if opts.start:
        cmd += ["-ss", opts.start]
    cmd += ["-i", str(src)]
    if opts.duration:
        cmd += ["-t", opts.duration]
    if opts.scale:
        cmd += ["-vf", f"scale={opts.scale.replace('x', ':')}"]
    cmd += _video_codec(out_fmt, opts) + [str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=VIDEO_FORMATS,
    outputs=AUDIO_FORMATS,
    requires=("ffmpeg",),
    category="video",
    priority=10,
)
def video_to_audio(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if opts.start:
        cmd += ["-ss", opts.start]
    cmd += ["-i", str(src), "-vn"]
    if opts.duration:
        cmd += ["-t", opts.duration]
    cmd += ffmpeg_audio_codec(out_fmt, opts) + [str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=VIDEO_FORMATS,
    outputs=("png", "jpg", "bmp", "tiff"),
    requires=("ffmpeg",),
    category="video",
    priority=15,
)
def video_to_frame(src: Path, dst: Path, opts: Opts) -> None:
    """Extract a single frame at --start (default: 1s in)."""
    out_fmt = dst.suffix.lstrip(".").lower()
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    cmd += ["-i", str(src)]
    if opts.start:
        cmd += ["-ss", opts.start]
    cmd += ["-frames:v", "1"]
    vf_parts: list[str] = []
    if opts.scale:
        vf_parts.append(f"scale={opts.scale.replace('x', ':')}")
    if out_fmt in ("jpg", "jpeg"):
        vf_parts.append("format=yuvj420p")
    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts)]
    cmd += [str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=VIDEO_FORMATS,
    outputs=("gif",),
    requires=("ffmpeg",),
    category="video",
    priority=10,
)
def video_to_gif(src: Path, dst: Path, opts: Opts) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if opts.start:
        cmd += ["-ss", opts.start]
    cmd += ["-i", str(src)]
    if opts.duration:
        cmd += ["-t", opts.duration]
    fps = {"low": "8", "medium": "12", "high": "20"}[opts.quality]
    scale = opts.scale.replace("x", ":") if opts.scale else "480:-1"
    cmd += ["-vf", f"fps={fps},scale={scale}:flags=lanczos", str(dst)]
    run(cmd, verbose=opts.verbose)
