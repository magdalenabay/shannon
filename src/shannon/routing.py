from __future__ import annotations

import shutil
import tempfile
from collections import deque
from pathlib import Path

from .installer import resolve_tool
from .registry import ConverterSpec, all_specs, find_direct
from .types import Opts


def find_chain(
    in_fmt: str,
    out_fmt: str,
    *,
    max_hops: int = 3,
    prefer_category: str | None = None,
) -> tuple[list[str], list[ConverterSpec]] | None:
    """Find a chain of converters from in_fmt → out_fmt.

    Returns (format_path, converter_specs) or None.
    format_path includes both endpoints; len(specs) == len(format_path) - 1.
    """
    if in_fmt == out_fmt:
        return ([in_fmt], [])

    direct = find_direct(in_fmt, out_fmt, prefer_category=prefer_category)
    if direct:
        return ([in_fmt, out_fmt], [direct[0]])

    specs_all = all_specs()
    queue: deque[tuple[str, list[str], list[ConverterSpec]]] = deque(
        [(in_fmt, [in_fmt], [])]
    )
    visited: set[str] = {in_fmt}
    while queue:
        cur, fmt_path, spec_path = queue.popleft()
        if len(spec_path) >= max_hops:
            continue
        for spec in specs_all:
            if cur not in spec.inputs:
                continue
            for next_fmt in spec.outputs:
                if next_fmt == out_fmt:
                    return (fmt_path + [next_fmt], spec_path + [spec])
                if next_fmt not in visited:
                    visited.add(next_fmt)
                    queue.append((next_fmt, fmt_path + [next_fmt], spec_path + [spec]))
    return None


def missing_tools(specs: list[ConverterSpec]) -> list[str]:
    seen: list[str] = []
    for s in specs:
        for r in s.requires:
            if r not in seen and resolve_tool(r) is None:
                seen.append(r)
    return seen


def execute_chain(
    specs: list[ConverterSpec],
    src: Path,
    dst: Path,
    opts: Opts,
    fmt_chain: list[str],
) -> None:
    if not specs:
        if src.resolve() != dst.resolve():
            shutil.copyfile(src, dst)
        return
    if len(specs) == 1:
        specs[0].func(src, dst, opts)
        return
    with tempfile.TemporaryDirectory(prefix="shannon-") as td:
        td_path = Path(td)
        cur_src = src
        for i, spec in enumerate(specs):
            if i == len(specs) - 1:
                spec.func(cur_src, dst, opts)
            else:
                next_fmt = fmt_chain[i + 1]
                # Construct a safe intermediate filename
                safe_fmt = next_fmt.replace(".", "_")
                tmp_out = td_path / f"hop{i}.{safe_fmt}"
                # For compound extensions, keep them as-is
                if next_fmt in ("tar.gz", "tar.xz", "tar.bz2"):
                    tmp_out = td_path / f"hop{i}.{next_fmt}"
                spec.func(cur_src, tmp_out, opts)
                cur_src = tmp_out
