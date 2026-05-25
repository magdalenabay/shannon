from __future__ import annotations

from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


EBOOK_FORMATS = (
    "epub",
    "mobi",
    "azw3",
    "fb2",
    "lit",
    "lrf",
    "pdb",
    "rtf",
    "snb",
    "tcr",
    "txt",
    "html",
    "pdf",
)


@register(
    inputs=EBOOK_FORMATS,
    outputs=EBOOK_FORMATS,
    requires=("ebook-convert",),
    category="ebook",
    priority=5,
    heavy=True,
)
def ebook_convert(src: Path, dst: Path, opts: Opts) -> None:
    cmd = ["ebook-convert", str(src), str(dst)]
    run(cmd, verbose=opts.verbose)
