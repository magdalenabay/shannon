from __future__ import annotations

import tempfile
from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


@register(
    inputs=("pdf",),
    outputs=("txt",),
    requires=("pdftotext",),
    category="pdf",
    priority=10,
)
def pdf_to_txt(src: Path, dst: Path, opts: Opts) -> None:
    cmd = ["pdftotext", "-layout", str(src), str(dst)]
    run(cmd, verbose=opts.verbose)


@register(
    inputs=("pdf",),
    outputs=("png", "jpg"),
    requires=("pdftoppm",),
    category="pdf",
    priority=10,
)
def pdf_to_image(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    fmt_flag = "-png" if out_fmt == "png" else "-jpeg"
    with tempfile.TemporaryDirectory(prefix="shannon-pdf-") as td:
        prefix = Path(td) / "page"
        cmd = [
            "pdftoppm",
            fmt_flag,
            "-r",
            "150",
            "-f",
            "1",
            "-l",
            "1",
            str(src),
            str(prefix),
        ]
        run(cmd, verbose=opts.verbose)
        for p in sorted(Path(td).iterdir()):
            if p.suffix.lower() in (".png", ".jpg", ".jpeg"):
                p.replace(dst)
                return
    raise RuntimeError("pdftoppm produced no output")


@register(
    inputs=("png", "jpg", "tiff"),
    outputs=("pdf",),
    requires=("img2pdf",),
    category="pdf",
    priority=10,
)
def image_to_pdf(src: Path, dst: Path, opts: Opts) -> None:
    cmd = ["img2pdf", str(src), "-o", str(dst)]
    run(cmd, verbose=opts.verbose)
