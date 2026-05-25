from __future__ import annotations

from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


OFFICE_FORMATS = (
    "docx",
    "xlsx",
    "pptx",
    "odt",
    "ods",
    "odp",
    "pdf",
    "rtf",
    "doc",
    "xls",
    "ppt",
    "html",
    "txt",
)


@register(
    inputs=OFFICE_FORMATS,
    outputs=OFFICE_FORMATS,
    requires=("soffice",),
    category="office",
    priority=5,
    heavy=True,
)
def office_to_office(src: Path, dst: Path, opts: Opts) -> None:
    out_fmt = dst.suffix.lstrip(".").lower()
    outdir = dst.parent
    cmd = [
        "soffice",
        "--headless",
        "--convert-to",
        out_fmt,
        "--outdir",
        str(outdir),
        str(src),
    ]
    run(cmd, verbose=opts.verbose)
    expected = outdir / (src.stem + "." + out_fmt)
    if expected.resolve() != dst.resolve() and expected.exists():
        expected.replace(dst)
