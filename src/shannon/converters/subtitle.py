from __future__ import annotations

from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


SUB_FORMATS = ("srt", "vtt", "ass", "ssa", "sub")


@register(
    inputs=SUB_FORMATS,
    outputs=SUB_FORMATS,
    requires=("ffmpeg",),
    category="subtitle",
    priority=10,
)
def subtitle_convert(src: Path, dst: Path, opts: Opts) -> None:
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), str(dst)]
    run(cmd, verbose=opts.verbose)
