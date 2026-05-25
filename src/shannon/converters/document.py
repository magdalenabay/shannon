from __future__ import annotations

from pathlib import Path

from ..registry import register
from ..runner import run
from ..types import Opts


DOC_FORMATS = (
    "md",
    "html",
    "rst",
    "tex",
    "txt",
    "epub",
    "docx",
    "odt",
)


@register(
    inputs=DOC_FORMATS,
    outputs=DOC_FORMATS,
    requires=("pandoc",),
    category="document",
    priority=10,
)
def doc_to_doc(src: Path, dst: Path, opts: Opts) -> None:
    cmd = ["pandoc", str(src), "-o", str(dst)]
    run(cmd, verbose=opts.verbose)


# Pandoc -> PDF via LaTeX is not assumed installed; route PDF via libreoffice instead.
