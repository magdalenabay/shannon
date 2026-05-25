from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from . import converters as _converters  # noqa: F401 — registers all converters
from .detect import from_extension, parse_target
from .installer import (
    HEAVY_BACKENDS,
    install_all,
    install_command_for,
    install_tool,
    resolve_tool,
)
from .platform import detect as platform_detect
from .registry import all_backends, all_specs
from .routing import execute_chain, find_chain, missing_tools
from .runner import ConvertError
from .types import Opts


__version__ = "0.1.0"


def cmd_list() -> int:
    by_cat: dict[str, list] = {}
    for s in all_specs():
        by_cat.setdefault(s.category, []).append(s)
    for cat in sorted(by_cat):
        print(f"\n[{cat}]")
        for s in sorted(by_cat[cat], key=lambda x: x.name):
            ins = ",".join(s.inputs)
            outs = ",".join(s.outputs)
            heavy = " (heavy)" if s.heavy else ""
            req = ("  requires: " + ",".join(s.requires)) if s.requires else ""
            print(f"  {s.name}: {ins} -> {outs}{heavy}{req}")
    return 0


def cmd_doctor() -> int:
    info = platform_detect()
    print(f"Platform: {info.os} ({info.arch})")
    pm = info.pkg_mgr.value
    pm_path = f" ({info.pkg_mgr_path})" if info.pkg_mgr_path else ""
    print(f"Package manager: {pm}{pm_path}\n")
    print("Backends:")
    backends = all_backends()
    rows: list[tuple[bool, str, set[str]]] = []
    for tool, cats in backends.items():
        rows.append((resolve_tool(tool) is not None, tool, cats))
    rows.sort(key=lambda r: (not r[0], r[1]))
    for present, tool, cats in rows:
        mark = "✓" if present else "✗"
        suffix = ""
        if not present:
            cmd = install_command_for(tool, info.pkg_mgr)
            if cmd:
                suffix = f"  -> {' '.join(cmd)}"
            else:
                suffix = "  (no recipe for this platform)"
        heavy = " [heavy]" if tool in HEAVY_BACKENDS else ""
        print(f"  {mark} {tool:<14} [{','.join(sorted(cats))}]{heavy}{suffix}")
    print(
        "\nRun `shannon --install-all` for light backends, or"
        " `--install-all --heavy` to include heavyweights."
    )
    return 0


def cmd_install_all(args: argparse.Namespace) -> int:
    return install_all(auto_yes=args.yes, heavy=args.heavy)


def _category_preference(opts: Opts) -> str | None:
    if opts.ocr:
        return "ocr"
    return None


def do_convert(
    inputs: list[Path],
    target: str,
    opts: Opts,
    *,
    auto_yes: bool = False,
    allow_heavy: bool = False,
    dry_run: bool = False,
) -> int:
    if len(inputs) > 1:
        # Output must be a bare format
        looks_like_path = (
            "/" in target or "\\" in target or target.startswith("~") or "." in target
        )
        if looks_like_path and target.lower() not in (
            "tar.gz",
            "tar.xz",
            "tar.bz2",
        ):
            print(
                "error: batch (multiple inputs) requires output to be a format,"
                " not a path or filename",
                file=sys.stderr,
            )
            return 2

    rc = 0
    for src in inputs:
        if not src.exists():
            print(f"error: input not found: {src}", file=sys.stderr)
            rc = 2
            continue
        out_path, out_fmt = parse_target(target, src)
        in_fmt = from_extension(src)
        if not in_fmt:
            print(f"error: cannot detect input format for {src}", file=sys.stderr)
            rc = 2
            continue
        if not out_fmt:
            print(
                f"error: cannot detect output format for {target}",
                file=sys.stderr,
            )
            rc = 2
            continue

        chain = find_chain(
            in_fmt, out_fmt, prefer_category=_category_preference(opts)
        )
        if chain is None:
            print(f"error: no path from {in_fmt} -> {out_fmt}", file=sys.stderr)
            print("  run `shannon --list` to see supported pairs", file=sys.stderr)
            rc = 2
            continue
        fmt_path, spec_chain = chain
        if not spec_chain:
            if src.resolve() != out_path.resolve():
                shutil.copyfile(src, out_path)
            print(f"  (no conversion needed) {src} -> {out_path}")
            continue

        for tool in missing_tools(spec_chain):
            ok = install_tool(tool, auto_yes=auto_yes, allow_heavy=allow_heavy)
            if not ok:
                print(f"error: cannot proceed without {tool}", file=sys.stderr)
                return 3

        chain_str = " -> ".join(fmt_path)
        if dry_run:
            print(f"[dry-run] {src} -> {out_path}  ({chain_str})")
            continue

        if len(spec_chain) > 1:
            print(f"  converting {src.name} via {chain_str}")
        else:
            print(f"  converting {src.name} -> {out_path.name}")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            execute_chain(spec_chain, src, out_path, opts, fmt_path)
            if not out_path.exists():
                print(
                    f"  ✗ tool exited cleanly but produced no output at {out_path}",
                    file=sys.stderr,
                )
                rc = 4
                continue
            print(f"  ✓ {out_path}")
        except ConvertError as e:
            print(f"  ✗ {e}", file=sys.stderr)
            rc = 4
        except Exception as e:
            print(f"  ✗ {type(e).__name__}: {e}", file=sys.stderr)
            rc = 4
    return rc


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="shannon",
        description="Universal file conversion CLI.",
        epilog=(
            "Examples:\n"
            "  shannon file.mp4 mp3              extract audio next to source\n"
            "  shannon *.heic jpg                batch convert\n"
            "  shannon doc.txt docx              use pandoc\n"
            "  shannon scan.pdf txt --ocr        OCR a scanned PDF\n"
            "  shannon clip.webm wav --quality high\n"
            "  shannon --doctor                  see backend status\n"
            "  shannon --install-all             install light backends\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "args",
        nargs="*",
        help="<input>... <target-format-or-output-path>",
    )
    p.add_argument("--list", action="store_true", help="list supported conversions")
    p.add_argument("--doctor", action="store_true", help="show backend install status")
    p.add_argument(
        "--install-all", action="store_true", help="install all light backends"
    )
    p.add_argument(
        "--heavy",
        action="store_true",
        help="include heavy backends (libreoffice, calibre)",
    )
    p.add_argument(
        "--quality",
        choices=["low", "medium", "high"],
        default="medium",
        help="quality preset (default: medium)",
    )
    p.add_argument("--start", help="audio/video start time (e.g. 0:10)")
    p.add_argument("--duration", help="audio/video duration (e.g. 5)")
    p.add_argument("--scale", help="image/video scale (e.g. 1920x1080)")
    p.add_argument(
        "--ocr",
        action="store_true",
        help="use OCR for image/PDF to text",
    )
    p.add_argument("--fast", action="store_true", help="favor speed over quality")
    p.add_argument("--dry-run", action="store_true", help="show what would happen")
    p.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="auto-accept install prompts",
    )
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument(
        "--version", action="version", version=f"shannon {__version__}"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    # parse_intermixed_args lets users put flags anywhere in the command line.
    args = parser.parse_intermixed_args(argv)

    if args.list:
        return cmd_list()
    if args.doctor:
        return cmd_doctor()
    if args.install_all:
        return cmd_install_all(args)

    if len(args.args) < 2:
        parser.print_help()
        return 1

    inputs = [Path(p).expanduser() for p in args.args[:-1]]
    target = args.args[-1]
    opts = Opts(
        quality=args.quality,
        start=args.start,
        duration=args.duration,
        scale=args.scale,
        ocr=args.ocr,
        fast=args.fast,
        heavy=args.heavy,
        verbose=args.verbose,
    )
    return do_convert(
        inputs,
        target,
        opts,
        auto_yes=args.yes,
        allow_heavy=args.heavy,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
