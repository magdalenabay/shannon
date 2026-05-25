from __future__ import annotations

import tarfile
import tempfile
import zipfile
from pathlib import Path

from ..installer import resolve_tool
from ..registry import register
from ..runner import run
from ..types import Opts


NATIVE_ARCHIVES = ("zip", "tar", "tar.gz", "tar.xz", "tar.bz2")
ALL_ARCHIVES = NATIVE_ARCHIVES + ("7z",)


def _sevenzip() -> str:
    name = resolve_tool("7z")
    if name is None:
        raise RuntimeError("7z/7zz not found")
    return name


def _fmt_of(path: Path) -> str:
    name = path.name.lower()
    for c in ("tar.gz", "tar.xz", "tar.bz2"):
        if name.endswith("." + c):
            return c
    return path.suffix.lower().lstrip(".")


def _extract(src: Path, dst_dir: Path) -> None:
    fmt = _fmt_of(src)
    if fmt == "zip":
        with zipfile.ZipFile(src) as z:
            z.extractall(dst_dir)
    elif fmt in ("tar", "tar.gz", "tar.xz", "tar.bz2"):
        with tarfile.open(src) as t:
            t.extractall(dst_dir)
    elif fmt == "7z":
        run([_sevenzip(), "x", "-y", f"-o{dst_dir}", str(src)])
    elif fmt == "rar":
        run(["unrar", "x", "-o+", str(src), str(dst_dir) + "/"])
    else:
        raise ValueError(f"unsupported archive: {src}")


def _create(src_dir: Path, dst: Path, fmt: str) -> None:
    if fmt == "zip":
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as z:
            for p in src_dir.rglob("*"):
                if p.is_file():
                    z.write(p, p.relative_to(src_dir))
    elif fmt == "tar":
        with tarfile.open(dst, "w") as t:
            t.add(src_dir, arcname=".")
    elif fmt == "tar.gz":
        with tarfile.open(dst, "w:gz") as t:
            t.add(src_dir, arcname=".")
    elif fmt == "tar.xz":
        with tarfile.open(dst, "w:xz") as t:
            t.add(src_dir, arcname=".")
    elif fmt == "tar.bz2":
        with tarfile.open(dst, "w:bz2") as t:
            t.add(src_dir, arcname=".")
    elif fmt == "7z":
        run([_sevenzip(), "a", "-y", str(dst.resolve()), "."], cwd=src_dir)
    else:
        raise ValueError(f"unsupported output: {fmt}")


def _do_repack(src: Path, dst: Path) -> None:
    out_fmt = _fmt_of(dst)
    with tempfile.TemporaryDirectory(prefix="shannon-arch-") as td:
        td_path = Path(td)
        _extract(src, td_path)
        _create(td_path, dst, out_fmt)


@register(
    inputs=NATIVE_ARCHIVES,
    outputs=NATIVE_ARCHIVES,
    requires=(),
    category="archive",
    priority=10,
)
def archive_native(src: Path, dst: Path, opts: Opts) -> None:
    _do_repack(src, dst)


@register(
    inputs=("7z",),
    outputs=ALL_ARCHIVES,
    requires=("7z",),
    category="archive",
    priority=10,
)
def archive_from_7z(src: Path, dst: Path, opts: Opts) -> None:
    _do_repack(src, dst)


@register(
    inputs=NATIVE_ARCHIVES,
    outputs=("7z",),
    requires=("7z",),
    category="archive",
    priority=10,
)
def archive_to_7z(src: Path, dst: Path, opts: Opts) -> None:
    _do_repack(src, dst)


@register(
    inputs=("rar",),
    outputs=NATIVE_ARCHIVES,
    requires=("unrar",),
    category="archive",
    priority=10,
)
def archive_from_rar(src: Path, dst: Path, opts: Opts) -> None:
    _do_repack(src, dst)


@register(
    inputs=("rar",),
    outputs=("7z",),
    requires=("unrar", "7z"),
    category="archive",
    priority=10,
)
def archive_from_rar_to_7z(src: Path, dst: Path, opts: Opts) -> None:
    _do_repack(src, dst)
