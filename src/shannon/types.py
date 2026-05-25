from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Opts:
    quality: str = "medium"
    start: str | None = None
    duration: str | None = None
    scale: str | None = None
    ocr: bool = False
    fast: bool = False
    heavy: bool = False
    verbose: bool = False
