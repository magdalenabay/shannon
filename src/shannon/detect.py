from __future__ import annotations

from pathlib import Path


ALIASES = {
    "jpeg": "jpg",
    "tif": "tiff",
    "yml": "yaml",
    "htm": "html",
    "tgz": "tar.gz",
    "txz": "tar.xz",
    "tbz2": "tar.bz2",
    "tbz": "tar.bz2",
}

COMPOUND = ("tar.gz", "tar.xz", "tar.bz2")


def from_extension(path: Path) -> str:
    name = path.name.lower()
    for c in COMPOUND:
        if name.endswith("." + c):
            return c
    ext = path.suffix.lower().lstrip(".")
    return ALIASES.get(ext, ext)


def parse_target(target: str, src: Path) -> tuple[Path, str]:
    """Resolve user-provided target into (output_path, output_format).

    Rules:
      - Path-like (contains / \\ or starts with ~): treat as full path.
      - Compound extension (tar.gz/tar.xz/tar.bz2): place next to src.
      - Plain extension (mp3, jpg, etc.): place next to src, swap extension.
      - Filename with dot (out.mp3): place in current working directory.
    """
    if "/" in target or "\\" in target or target.startswith("~"):
        out = Path(target).expanduser()
        return out, from_extension(out)

    low = target.lower()
    if low in COMPOUND:
        return src.parent / (src.stem + "." + low), low

    if "." not in target:
        fmt = ALIASES.get(low, low)
        # Strip any compound suffix already on src
        stem = src.name
        for c in COMPOUND:
            if stem.lower().endswith("." + c):
                stem = stem[: -(len(c) + 1)]
                return src.parent / (stem + "." + fmt), fmt
        return src.with_suffix("." + fmt), fmt

    out = Path(target)
    return out, from_extension(out)
