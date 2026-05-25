from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

from .platform import PkgMgr, detect
from .runner import run, ConvertError


INSTALL_MAP: dict[str, dict[PkgMgr, list[str] | None]] = {
    "ffmpeg": {
        PkgMgr.BREW: ["brew", "install", "ffmpeg"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "ffmpeg"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "ffmpeg"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "ffmpeg"],
        PkgMgr.WINGET: ["winget", "install", "--id", "Gyan.FFmpeg", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "ffmpeg"],
    },
    "lame": {
        PkgMgr.BREW: ["brew", "install", "lame"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "lame"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "lame"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "lame"],
        PkgMgr.WINGET: ["winget", "install", "--id", "RareWares.LAME", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "lame"],
    },
    "magick": {
        PkgMgr.BREW: ["brew", "install", "imagemagick"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "imagemagick"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "ImageMagick"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "imagemagick"],
        PkgMgr.WINGET: ["winget", "install", "--id", "ImageMagick.ImageMagick", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "imagemagick"],
    },
    "cwebp": {
        PkgMgr.BREW: ["brew", "install", "webp"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "webp"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "libwebp-tools"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "libwebp"],
        PkgMgr.WINGET: None,
        PkgMgr.SCOOP: ["scoop", "install", "libwebp"],
    },
    "dwebp": {
        PkgMgr.BREW: ["brew", "install", "webp"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "webp"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "libwebp-tools"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "libwebp"],
        PkgMgr.WINGET: None,
        PkgMgr.SCOOP: ["scoop", "install", "libwebp"],
    },
    "avifenc": {
        PkgMgr.BREW: ["brew", "install", "libavif"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "libavif-bin"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "libavif-tools"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "libavif"],
        PkgMgr.WINGET: None,
        PkgMgr.SCOOP: None,
    },
    "heif-convert": {
        PkgMgr.BREW: ["brew", "install", "libheif"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "libheif-examples"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "libheif-tools"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "libheif"],
        PkgMgr.WINGET: None,
        PkgMgr.SCOOP: None,
    },
    "pandoc": {
        PkgMgr.BREW: ["brew", "install", "pandoc"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "pandoc"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "pandoc"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "pandoc"],
        PkgMgr.WINGET: ["winget", "install", "--id", "JohnMacFarlane.Pandoc", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "pandoc"],
    },
    "soffice": {
        PkgMgr.BREW: ["brew", "install", "--cask", "libreoffice"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "libreoffice"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "libreoffice"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "libreoffice-fresh"],
        PkgMgr.WINGET: [
            "winget",
            "install",
            "--id",
            "TheDocumentFoundation.LibreOffice",
            "--silent",
        ],
        PkgMgr.SCOOP: ["scoop", "install", "libreoffice"],
    },
    "pdftotext": {
        PkgMgr.BREW: ["brew", "install", "poppler"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "poppler-utils"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "poppler-utils"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "poppler"],
        PkgMgr.WINGET: ["winget", "install", "--id", "oschwartz10612.Poppler", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "poppler"],
    },
    "pdftoppm": {
        PkgMgr.BREW: ["brew", "install", "poppler"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "poppler-utils"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "poppler-utils"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "poppler"],
        PkgMgr.WINGET: ["winget", "install", "--id", "oschwartz10612.Poppler", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "poppler"],
    },
    "qpdf": {
        PkgMgr.BREW: ["brew", "install", "qpdf"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "qpdf"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "qpdf"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "qpdf"],
        PkgMgr.WINGET: ["winget", "install", "--id", "qpdf.qpdf", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "qpdf"],
    },
    "img2pdf": {
        PkgMgr.BREW: ["brew", "install", "img2pdf"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "img2pdf"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "img2pdf"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "img2pdf"],
        PkgMgr.WINGET: None,
        PkgMgr.SCOOP: None,
    },
    "tesseract": {
        PkgMgr.BREW: ["brew", "install", "tesseract"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "tesseract-ocr"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "tesseract"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "tesseract"],
        PkgMgr.WINGET: ["winget", "install", "--id", "UB-Mannheim.TesseractOCR", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "tesseract"],
    },
    "ebook-convert": {
        PkgMgr.BREW: ["brew", "install", "--cask", "calibre"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "calibre"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "calibre"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "calibre"],
        PkgMgr.WINGET: ["winget", "install", "--id", "calibre.calibre", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "calibre"],
    },
    "7z": {
        PkgMgr.BREW: ["brew", "install", "sevenzip"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "p7zip-full"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "p7zip"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "p7zip"],
        PkgMgr.WINGET: ["winget", "install", "--id", "7zip.7zip", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "7zip"],
    },
    "unrar": {
        PkgMgr.BREW: ["brew", "install", "carlocab/personal/unrar"],
        PkgMgr.APT: ["sudo", "apt-get", "install", "-y", "unrar"],
        PkgMgr.DNF: ["sudo", "dnf", "install", "-y", "unrar"],
        PkgMgr.PACMAN: ["sudo", "pacman", "-S", "--noconfirm", "unrar"],
        PkgMgr.WINGET: ["winget", "install", "--id", "RARLab.WinRAR", "--silent"],
        PkgMgr.SCOOP: ["scoop", "install", "unrar"],
    },
}


HEAVY_BACKENDS = {"soffice", "ebook-convert"}


# Some tools are known by multiple binary names across platforms.
# When checking for installation, accept any. When installing, use the
# recipe keyed on the canonical name.
TOOL_ALIASES: dict[str, list[str]] = {
    "7z": ["7zz", "7z"],
}


def resolve_tool(name: str) -> str | None:
    """Return the first binary alias that is installed for `name`, or None."""
    for cand in TOOL_ALIASES.get(name, [name]):
        if shutil.which(cand):
            return cand
    return None


def state_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME")
    p = Path(base) if base else (Path.home() / ".config")
    p = p / "shannon"
    p.mkdir(parents=True, exist_ok=True)
    return p


def state_file() -> Path:
    return state_dir() / "state.json"


def load_state() -> dict:
    f = state_file()
    if not f.exists():
        return {"installed_by_shannon": []}
    try:
        return json.loads(f.read_text())
    except Exception:
        return {"installed_by_shannon": []}


def save_state(state: dict) -> None:
    state_file().write_text(json.dumps(state, indent=2))


def confirm(prompt: str, *, default_yes: bool = True, auto_yes: bool = False) -> bool:
    if auto_yes:
        return True
    if not sys.stdin.isatty():
        return False
    suffix = "[Y/n]" if default_yes else "[y/N]"
    try:
        ans = input(f"{prompt} {suffix} ").strip().lower()
    except EOFError:
        return False
    if not ans:
        return default_yes
    return ans in ("y", "yes")


def install_command_for(tool: str, pkg_mgr: PkgMgr) -> list[str] | None:
    return INSTALL_MAP.get(tool, {}).get(pkg_mgr)


def install_tool(
    tool: str, *, auto_yes: bool = False, allow_heavy: bool = False
) -> bool:
    if resolve_tool(tool):
        return True
    info = detect()
    if info.pkg_mgr == PkgMgr.NONE:
        print(f"✗ {tool}: no supported package manager on {info.os}", file=sys.stderr)
        return False
    cmd = install_command_for(tool, info.pkg_mgr)
    if cmd is None:
        print(
            f"✗ {tool}: no install recipe for {info.pkg_mgr.value} on {info.os}",
            file=sys.stderr,
        )
        return False
    if tool in HEAVY_BACKENDS and not allow_heavy:
        print(
            f"✗ {tool} is a heavy backend — pass --heavy to install",
            file=sys.stderr,
        )
        return False
    if not confirm(
        f"Install {tool} via {info.pkg_mgr.value}? ({' '.join(cmd)})",
        auto_yes=auto_yes,
    ):
        return False
    try:
        run(cmd, verbose=True)
    except ConvertError as e:
        print(f"✗ install failed: {e}", file=sys.stderr)
        return False
    state = load_state()
    if tool not in state["installed_by_shannon"]:
        state["installed_by_shannon"].append(tool)
        save_state(state)
    return resolve_tool(tool) is not None


def install_all(*, auto_yes: bool = False, heavy: bool = False) -> int:
    from .registry import all_backends

    info = detect()
    if info.pkg_mgr == PkgMgr.NONE:
        print(f"No supported package manager found on {info.os}.", file=sys.stderr)
        return 1
    print(
        f"Platform: {info.os} ({info.arch})  |  Package manager: {info.pkg_mgr.value}\n"
    )
    missing: list[str] = []
    for tool in sorted(all_backends()):
        if not resolve_tool(tool):
            if tool in HEAVY_BACKENDS and not heavy:
                continue
            missing.append(tool)
    if not missing:
        print("All backends already installed.")
        return 0
    print(f"Installing {len(missing)} backend(s): {', '.join(missing)}\n")
    failed: list[str] = []
    for tool in missing:
        if not install_tool(tool, auto_yes=auto_yes, allow_heavy=heavy):
            failed.append(tool)
    print()
    if failed:
        print(f"Failed: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("All requested backends installed.")
    return 0
