from __future__ import annotations

import tempfile
from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


IMG_FORMATS = ("png", "jpg", "tiff", "bmp")


@register(
    inputs=IMG_FORMATS,
    outputs=("txt",),
    requires=("tesseract",),
    category="ocr",
    priority=10,
)
def image_ocr_txt(src: Path, dst: Path, opts: Opts) -> None:
    out_base = dst.with_suffix("")
    cmd = ["tesseract", str(src), str(out_base)]
    run(cmd, verbose=opts.verbose)
    produced = Path(str(out_base) + ".txt")
    if produced.resolve() != dst.resolve() and produced.exists():
        produced.replace(dst)


@register(
    inputs=("pdf",),
    outputs=("txt",),
    requires=("tesseract", "pdftoppm"),
    category="ocr",
    priority=5,
)
def pdf_ocr_txt(src: Path, dst: Path, opts: Opts) -> None:
    with tempfile.TemporaryDirectory(prefix="shannon-ocr-") as td:
        td_path = Path(td)
        run(
            [
                "pdftoppm",
                "-png",
                "-r",
                "300",
                str(src),
                str(td_path / "page"),
            ],
            verbose=opts.verbose,
        )
        all_text: list[str] = []
        for img in sorted(td_path.glob("page-*.png")):
            base = img.with_suffix("")
            run(["tesseract", str(img), str(base)], verbose=opts.verbose)
            txt = Path(str(base) + ".txt")
            if txt.exists():
                all_text.append(txt.read_text())
        dst.write_text("\n\n".join(all_text))
